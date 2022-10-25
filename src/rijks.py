from typing import Optional, Tuple
import os
import math
import requests
import asyncio
import json
import time
import httpx
import pandas as pd
from xml.etree import ElementTree as ET
from datetime import datetime
from src.utils import find_existing_files


def get_key() -> str:
    return "Yiv3t0C0"


def get_page(session, url: str, page_nr: Optional[int] = None):
    if page_nr is not None:
        url += f"&p={page_nr}"
    res = session.get(url)
    data = res.json()
    return data


def rijks_find_results(query: str, lang: str = "en"):
    key = get_key()
    n_results = 100
    url = f"https://www.rijksmuseum.nl/api/{lang}/collection?key={key}&ps={n_results}&q={query}"
    with requests.Session() as session:
        session.headers = {"Accept": "*/*"}
        first_page = get_page(session, url)
        print(
            f"Found {first_page['count']} results. Collecting object numbers. This may take a while, if there are a lot of results."
        )
        n_pages = math.ceil(int(first_page["count"]) / n_results)
        art_objects = first_page["artObjects"]
        for n in range(2, n_pages + 1):
            for attempts in range(4, -1, -1):
                try:
                    page = get_page(session, url, n)
                    art_objects.extend(page["artObjects"])
                    break
                except requests.JSONDecodeError:
                    wait_for = 10
                    print(
                        f"Rate limiter on request {n} / {n_pages} :( waiting for {wait_for} seconds. Trying again {attempts} times."
                    )
                    time.sleep(wait_for)
                    if attempts == 0:
                        raise Exception("Too many failures :( Please try again.")
                    continue
    return art_objects


def rijks_find_results_full(query, lang="en", overwrite=False):
    art_objects = rijks_find_results(query, lang)
    # print(json.dumps(art_objects, indent=2))
    object_nrs = [o["objectNumber"] for o in art_objects]
    return asyncio.run(fetch(object_nrs, overwrite=overwrite))


def rijks_find_object(object_nr: str, lang="en"):
    res = asyncio.run(find_object(object_nr, lang))
    if res is not None:
        art_object = res["artObject"]
        write_to_file(art_object, lang)
    return res


async def find_object(object_nr, lang="en"):
    async with httpx.AsyncClient(timeout=None) as client:
        res = await get_object(object_nr, client, lang)
    res = res[0]
    if res.status_code == 200:
        return res.json()
    print(f"Could not find object with id: {object_nr}")
    return None


async def get_object(object_nr, client, lang="en"):
    url = f"https://www.rijksmuseum.nl/api/{lang}/collection/{object_nr}"
    key = get_key()
    return (await client.get(f"{url}?key={key}"), object_nr)


async def fetch_all():
    df = pd.read_csv("rijks_harvest_complete_dataset.zip", sep=";")
    object_nrs = df["identifier"].tolist()
    await fetch(object_nrs)


async def fetch(object_nrs, lang="en", overwrite=False):
    try:
        out = []
        if not overwrite:
            file_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "json", "rijks", lang
            )
            existing_object_nrs = find_existing_files(file_path)
            cached_objects = [x for x in object_nrs if x in existing_object_nrs]
            object_nrs = [x for x in object_nrs if x not in existing_object_nrs]
            for object_nr in cached_objects:
                p = os.path.join(file_path, f"{object_nr}.json")
                with open(p) as f:
                    out.append(json.load(f))
            print(f"{len(cached_objects)} objects in cache.")

        async with httpx.AsyncClient(timeout=None) as client:
            n = 10
            wait_for_s = 30

            list_of_lists = [
                object_nrs[i : i + n] for i in range(0, len(object_nrs), n)
            ]
            # list_of_lists = [object_nrs[i : i + n] for i in range(0, 1000, n)]

            failures = []

            for count, list_of_ids in enumerate(list_of_lists):
                resps = await asyncio.gather(
                    *map(lambda x: get_object(x, client), list_of_ids),
                    asyncio.sleep(1),
                )
                resps.pop()
                data = []
                limiter = False
                for t in resps:
                    res, object_nr = t
                    if res is None:
                        print("This isn't supposed to happen.")
                    elif res.status_code == 200:
                        data.append(res.json())
                    else:
                        failures.append(object_nr)
                        if not limiter:
                            print(
                                f"Oops, hit rate limiter. Waiting {wait_for_s} seconds."
                            )
                            limiter = True
                            time.sleep(wait_for_s)

                for res in data:
                    art_object = res["artObject"]
                    out.append(art_object)
                    write_to_file(art_object, lang)

                print(f"Progress: {count + 1} / {len(list_of_lists)}")

            if len(failures) > 0:
                print(
                    f"Hit rate limiter with {len(failures)} objects! Fetching the skipped objects."
                )
                await fetch(failures, lang, overwrite)
        return out
    except RuntimeError:
        print("The server broke connection, please try again")
        return []


def write_to_file(art_object, lang="en"):
    file_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "json",
        "rijks",
        lang,
        f"{art_object['objectNumber']}.json",
    )
    with open(
        file_path,
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


if __name__ == "__main__":
    # asyncio.run(main())
    rijks_find_object("SK-C-5", "en")
    # asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    # rijks_find_results_full("green")
    # asyncio.run(fetch_all())
