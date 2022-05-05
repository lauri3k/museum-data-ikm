import json
import time
import asyncio
import httpx
from typing import List


async def get(object_nr, client):
    url = (
        f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{object_nr}"
    )
    return await client.get(url)


async def get_collection_ids(client) -> List[str]:
    url = "https://collectionapi.metmuseum.org/public/collection/v1/objects"
    res = await client.get(url)

    data = res.json()
    return data["objectIDs"]


async def fetch():
    async with httpx.AsyncClient(timeout=None) as client:
        object_ids = await get_collection_ids(client)
        n = 20
        # list_split = [object_ids[i : i + n] for i in range(0, len(object_ids), n)]
        list_split = [object_ids[i : i + n] for i in range(0, 1000, n)]

        for l in list_split:
            start = time.time()
            resps = await asyncio.gather(
                *map(lambda x: asyncio.ensure_future(get(x, client)), l),
                asyncio.sleep(0.25),
            )
            resps.pop()
            # data = [res.json() for res in resps if res.status_code == 200]
            data = []
            for res in resps:
                if res is None:
                    print("This isn't supposed to happen.")
                elif res.status_code == 200:
                    data.append(res.json())
                else:
                    print(res)
                    print(res.content)
                    # print(json.dumps(res.json()), indent=2)

            print(time.time() - start)

            for res in data:
                with open(
                    f"./json/met/{res['objectID']}.json", "w", encoding="utf-8"
                ) as f:
                    json.dump(res, f, indent=2)


async def main():
    start = time.time()
    await fetch()
    print(time.time() - start)


if __name__ == "__main__":
    asyncio.run(main())
