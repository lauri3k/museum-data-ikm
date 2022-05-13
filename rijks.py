from typing import Optional
import math
import requests

# from rijks_async import write_to_file

# from dotenv import load_dotenv
from rijks_harvest import get_key


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

    # for art_object in art_objects:
    #     write_to_file(art_object)

    return art_objects


def main():
    # load_dotenv()
    rijks_find_results("slave")


if __name__ == "__main__":
    main()
