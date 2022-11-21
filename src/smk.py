import math
import time
import requests
import json


def get_page(session, query, lang, offset, n_results):
    url = f"https://api.smk.dk/api/v1/art/search?keys={query}&offset={offset}&rows={n_results}&lang={lang}"
    res = session.get(url)
    return res.json()


def smk_find_results(query, lang="en"):
    n_results = 100
    offset = 0

    with requests.Session() as session:
        first_page = get_page(session, query, lang, offset, n_results)
        found = int(first_page["found"])
        print(f"Found {found} objects.")
        items = first_page["items"]
        n_pages = math.ceil(found / n_results)
        for n in range(1, n_pages):
            offset = n * n_results
            for attempts in range(4, -1, -1):
                try:
                    page = get_page(session, query, lang, offset, n_results)
                    # print(page["found"])
                    # print(json.dumps(page, indent=2))
                    items.extend(page["items"])
                    break
                except Exception as e:
                    wait_for = 10
                    print(
                        f"Something went wrong on request: {n} / {n_pages} :( waiting for {wait_for} seconds. Trying again {attempts} times."
                    )
                    time.sleep(wait_for)
                    if attempts == 0:
                        raise Exception("Too many failures :( Please try again.")
                    continue

        return items


if __name__ == "__main__":
    result = smk_find_results("green")
    print(len(result))
