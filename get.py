from typing import List, Dict
from bs4 import BeautifulSoup
from requests import get
from time import sleep
import urllib.parse
import logging
import json
import sys


def get_items() -> List[Dict]:
    items = []

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

        # Get product Webpage
        print("Getting", product["name"])
        product_path = d.a["href"]
        r = get(urllib.parse.urljoin(url, product_path))

        # Extract product description
        soup = BeautifulSoup(r.text, "html.parser")

        try:
            # Old product page, first <p> under div.lead
            # e.g. https://aws.amazon.com/cloudsearch/
            p = soup.select_one("div.lead p").text.strip()
        except AttributeError:
            # New product page, first <p>
            # e.g. https://aws.amazon.com/athena/
            try:
                p = soup.select_one("p").text.strip()
            except AttributeError:
                # The page is irregular, ignore (e.g. a beta)
                # e.g. https://docs.aws.amazon.com/honeycode/index.html
                print("Can't parse", product["name"])
                continue

        product["desc"] = p

        items.append(product)

    return items


def save_items(items, filename) -> None:
    with open(filename, "w") as f:
        f.write(json.dumps(items, indent=2, separators=(",", ": ")))


if __name__ == "__main__":
    items = get_items()
    filename = sys.argv[1]

    save_items(items, filename)
