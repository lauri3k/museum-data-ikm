from typing import Optional, Tuple
import math
import requests
import asyncio
import json
import time
import httpx
import pandas as pd
from xml.etree import ElementTree as ET
from datetime import datetime


def get_key() -> str:
    """
    Get API key from .env file.
    """
    return "Yiv3t0C0"
    # return os.getenv("RIJKSMUSEUM_API")


def get(url: str, page_nr: Optional[int] = None):
    if page_nr is not None:
        url += f"&p={page_nr}"
    res = requests.get(url)
    data = res.json()
    return data


def rijks_find_results(query: str, lang: str = "en"):
    key = get_key()
    n_results = 100
    url = f"https://www.rijksmuseum.nl/api/{lang}/collection?key={key}&ps={n_results}&q={query}"
    first_page = get(url)
    print(f"Found {first_page['count']} results.")
    n_pages = math.ceil(int(first_page["count"]) / n_results)
    art_objects = first_page["artObjects"]
    for n in range(2, n_pages + 1):
        page = get(url, n)
        art_objects.extend(page["artObjects"])
    return art_objects


def rijks_find_object(id: str, lang="en"):
    pass


async def get_object(object_nr, client, lang="en"):
    url = f"https://www.rijksmuseum.nl/api/{lang}/collection/{object_nr}"
    key = get_key()
    return await client.get(f"{url}?key={key}")


async def fetch():
    async with httpx.AsyncClient(timeout=None) as client:
        df = pd.read_csv("rijks_harvest_complete_dataset.csv", sep=",")
        n = 5
        list_df = [df[i : i + n] for i in range(0, df.shape[0], n)]
        # list_df = [df[i : i + n] for i in range(0, 1, n)]

        for l in list_df:
            start = time.time()
            resps = await asyncio.gather(
                *map(lambda x: get_object(x, client), l["identifier"]),
                asyncio.sleep(10),
            )
            resps.pop()
            data = []
            for res in resps:
                if res is None:
                    print("This isn't supposed to happen.")
                elif res.status_code == 200:
                    data.append(res.json())
                else:
                    print(res)
                    print(res.content)

            print(time.time() - start)

            for res in data:
                art_object = res["artObject"]
                write_to_file(art_object)


def write_to_file(art_object, lang="en"):
    with open(
        f"./json/rijks/{lang}/{art_object['objectNumber']}.json",
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(art_object, f, indent=2)


def harvest(token: Optional[str] = None, count: int = 0) -> Tuple[Optional[str], int]:
    """
    Get general information about the objects from the Object metadata harvesting API.
    https://data.rijksmuseum.nl/object-metadata/harvest/
    """
    key = get_key()
    url = (
        f"https://www.rijksmuseum.nl/api/oai/{key}?verb=ListRecords&metadataPrefix=dc"
        f"{f'&resumptionToken={token}' if token is not None else ''}"
    )

    res = requests.get(url)
    data = res.content.decode("utf-8")
    tree = ET.fromstring(data)
    # xml = ET.ElementTree(tree)

    namespaces = {
        "oai": "http://www.openarchives.org/OAI/2.0/",
        "oai_dc": "http://www.openarchives.org/OAI/2.0/oai_dc/",
        "dc": "http://purl.org/dc/elements/1.1/",
    }

    df: pd.DataFrame = pd.read_xml(data, xpath=".//oai_dc:dc", namespaces=namespaces)
    n_objects = df.shape[0]
    count += n_objects

    token = tree.find(".//oai:resumptionToken", namespaces=namespaces)
    total_n = token.attrib["completeListSize"]
    token = token.text if token is not None else None

    df.to_csv("rijks_harvest_complete_dataset.csv", index=False, mode="a")
    # xml.write("out.xml")

    if count % 1000 == 0:
        print(
            f"{timestamp()} - Progress: {round((int(count) / int(total_n) * 100.0), 2)}%"
        )
    return token, count


def timestamp() -> str:
    """Generate a timestamp"""
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def run_harvest() -> None:
    print(f"{timestamp()} - Starting harvesting")
    t, c = harvest()
    while t:
        t, c = harvest(t, c)
    print(f"{timestamp()} - All done!")


async def main():
    async with httpx.AsyncClient(timeout=None) as client:
        await get_object("SK-C-5", client)


if __name__ == "__main__":
    # asyncio.run(main())
    pass
