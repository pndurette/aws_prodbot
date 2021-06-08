import json
import sys
import urllib.parse
from time import sleep
from typing import Dict, List

from bs4 import BeautifulSoup
from requests import get

# The numbers of paragrahs of each product page to scrape
# The more we add, the less relevant it becomes
PARAGRAPHS = 1


def get_items() -> List[Dict]:
    items = []
    names = []

    # Get main Webpage
    url = "https://aws.amazon.com/products/"
    r = get(url)

    # Extract product <div> list, e.g.
    # <div class="lb-content-item">
    #   <a href="/cloudwatch/?c=15&amp;pt=1"> <i></i>
    #       <span>Amazon CloudWatch</span>
    #       <cite>Monitor Resources and Applications</cite>
    #   </a>
    # </div>
    soup = BeautifulSoup(r.text, "html.parser")
    divs = soup.findAll("div", class_="lb-content-item")

    # Structure
    # {<item name>: <item desc>}
    for d in divs:
        product = dict()
        sleep(1)

        # Title (name) and subtitle (blurb)
        product["name"] = d.a.span.text.strip()
        product["blurb"] = d.a.cite.text.strip()

        # Each product can exist in many main page
        # categories, ignore subsquent ones
        if product["name"] in names:
            continue

        # Get product Webpage
        print("Getting", product["name"])
        product_path = d.a["href"]
        r = get(urllib.parse.urljoin(url, product_path))

        # Extract product description
        soup = BeautifulSoup(r.text, "html.parser")

        # 1. Old product page, all <p> elements under div.lead
        # e.g. https://aws.amazon.com/cloudsearch/
        p = [x.text.strip() for x in soup.select("div.lead p")[:PARAGRAPHS]]

        if not p:
            # 2. New product page
            # No distinct structure, but the first <p> elements
            # Have the descriptions, take the first 2.
            # e.g. https://aws.amazon.com/athena/
            p = [x.text.strip() for x in soup.select("p")[:PARAGRAPHS]]

        # elif not p:
        #     # 3. The page is irregular, ignore (e.g. a beta)
        #     # e.g. https://docs.aws.amazon.com/honeycode/index.html
        #     print("Can't parse", product["name"])
        #     continue

        # try:
        #     # Old product page, first <p> under div.lead
        #     # e.g. https://aws.amazon.com/cloudsearch/
        #     # p = soup.select_one("div.lead p").text.strip()
        #     p = [x.text.strip() for x in soup.select("div.lead p")]
        # except AttributeError:
        #     # New product page, first <p>
        #     # e.g. https://aws.amazon.com/athena/
        #     try:
        #         # The main description is the only <div> that has this
        #         # color style set. Text is in the <p> elements.
        #         print("HERE")
        #         p = [x.text.strip() for x in soup.select("div[style='color:#232f3e;'] p")]
        #         print("HERE")
        #         print(p)
        #     except AttributeError:
        #         # The page is irregular, ignore (e.g. a beta)
        #         # e.g. https://docs.aws.amazon.com/honeycode/index.html
        #         print("Can't parse", product["name"])
        #         continue

        product["desc"] = " ".join(p)

        names.append(product["name"])

        items.append(product)

    return items


def save_items(items, filename) -> None:
    with open(filename, "w") as f:
        f.write(json.dumps(items, indent=2, separators=(",", ": ")))


if __name__ == "__main__":
    # Usage python get.py <json to save>

    items = get_items()
    filename = sys.argv[1]

    save_items(items, filename, lenght)
