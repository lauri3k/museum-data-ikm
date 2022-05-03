"""
Scripts for pulling data from Rijksmuseum API - https://data.rijksmuseum.nl/object-metadata/api/
"""
import json
import os
from typing import Optional, Any, Tuple
from xml.etree import ElementTree as ET
from datetime import datetime
import requests

import pandas as pd
from dotenv import load_dotenv


def get_key() -> str:
    """
    Get API key from .env file.
    """
    return os.getenv("RIJKSMUSEUM_API")


def get_info(object_nr: str) -> Any:
    """
    Get detailed information about a specific object, identified by object number.
    https://data.rijksmuseum.nl/object-metadata/api/#collection-details-api
    """
    url = f"https://www.rijksmuseum.nl/api/en/collection/{object_nr}"
    key = get_key()
    res = requests.get(f"{url}?key={key}")
    print(json.dumps(res.json(), indent=2))
    return res.json()


def harvest(token: Optional[str] = None, count: int = 0) -> Tuple[str, int]:
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

    df.to_csv("out.csv", index=False, mode="a", header=(not os.path.exists("out.csv")))
    # xml.write("out.xml")

    if count % 1000 == 0:
        print(
            f"{timestamp()} - Progress: {round((int(count) / int(total_n) * 100.0), 2)}%"
        )
    return token, count


def timestamp() -> str:
    """Generate a timestamp"""
    return datetime.now().strftime("%Y-%m-%d %H:%M")


if __name__ == "__main__":
    load_dotenv()

    print(f"{timestamp()} - Starting harvesting")
    t, c = harvest()
    while t:
        t, c = harvest(t, c)
    print(f"{timestamp()} - All done, hooray!")
