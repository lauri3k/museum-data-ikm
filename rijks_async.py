import asyncio
import json
import time
from dotenv import load_dotenv
import httpx
import pandas as pd
from rijks_harvest import get_key


async def get_object(object_nr, client):
    url = f"https://www.rijksmuseum.nl/api/en/collection/{object_nr}"
    key = get_key()
    return await client.get(f"{url}?key={key}")


async def fetch():
    async with httpx.AsyncClient(timeout=None) as client:

        df = pd.read_csv("rijks_harvest_complete_dataset.csv", sep=",")

        n = 5
        list_df = [df[i : i + n] for i in range(0, df.shape[0], n)]
        # list_df = [df[i : i + n] for i in range(0, 1000, n)]

        for l in list_df:
            start = time.time()
            resps = await asyncio.gather(
                *map(lambda x: get_object(x, client), l["identifier"]),
                asyncio.sleep(10),
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
                # print(json.dumps(res, indent=2))
                art_object = res["artObject"]

                # art_object.pop("colors", None)
                # art_object.pop("normalizedColors", None)
                # art_object.pop("colorsWithNormalization", None)
                # art_object.pop("normalized32Colors", None)

                write_to_file(art_object)


def write_to_file(art_object):
    with open(
        f"./json/rijks/{art_object['objectNumber']}.json",
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(art_object, f, indent=2)


async def main():
    load_dotenv()
    start = time.time()
    await fetch()
    print(time.time() - start)


if __name__ == "__main__":
    asyncio.run(main())
