from textwrap import indent
import requests
import asyncio
import json
from met_async import fetch


async def met_find_results(query: str):
    url = f"https://collectionapi.metmuseum.org/public/collection/v1/search?q={query}"
    res = requests.get(url)
    data = res.json()
    object_ids = data["objectIDs"]
    if object_ids is not None:
        print(f"Found {len(object_ids)} results.")
        results = await fetch(object_ids)
        return results
    print(f"Found 0 results.")
    return []


async def main():
    await met_find_results("slave")


if __name__ == "__main__":
    asyncio.run(main())
