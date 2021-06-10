import json
import html
import sys
import re
import urllib.parse
from urllib.parse import unquote
from time import sleep
from typing import Dict, List

from bs4 import BeautifulSoup
from requests import get

# This scripts extracts a list of product items dicts
# It is used by tweet.py to generate a corpus
# It only needs to be run to refresh aws.json,
# which is included in the Docker image

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


def get_docs_items() -> List[Dict]:
    # Main list of services
    items = []

    # List to keep track of already fetched products
    # to prevent fetching them more than once
    names = []

    # List of extra "sub-genre" names to add to the list of names
    # e.g. "Amazon Kinesis Data Firehose" or all the SageMakers
    extra_names = []

    # Get main Webpage docs XML
    main_url = "https://docs.aws.amazon.com"
    main_xml = get_page_xml(main_url)

    main_soup = BeautifulSoup(main_xml, "lxml")
    services = main_soup.find_all("service")

    """
    <tile>
    <title>AWS Management Console</title>
        <services>
            <service href="/awsconsolehelpdocs/latest/gsg/getting-started.html?id=docs_gateway">
            <prefix></prefix>
            <name>Getting Started with the Console</name>
            [...]
        </services>
    </tile>
    <tile>
    """

    # aka 'tiles'
    # Sections of https://docs.aws.amazon.com
    sections_to_skip = [
        "General Reference",
        "AWS Management Console",
        "SDKs & Toolkits",
        "Additional Resources",
    ]

    for s in services:
        service = {
            "name": "",
            "blurb": "",
            "abbreviation": "",
            "desc": ""
        }

        # Skip the sections that aren't products per se.
        # Section titles are HTML-escaped
        section_title = s.parent.parent.title.string
        if html.unescape(section_title) in sections_to_skip:
            continue

        # Service href
        # Skip absolute product links (non-docs sites)
        href = s["href"]
        if not href.startswith("/"):
            continue

        # Name in the main XML doc
        name = s.find("name").string

        # Each product can exist in many main page
        # section, ignore subsquent ones
        if name in names:
            continue

        # Link names ending in "Overview" aren't really names
        if name.endswith("Overview"):
            continue

        # Just a quick way to only query specifc products to test
        # if name not in ["Neptune"]:
        #     continue
        print(f"Processing {name}...")

        # Get service landing page
        sleep(0.5)
        service_url = urllib.parse.urljoin(main_url, href)
        service_xml = get_page_xml(service_url)
        if service_xml is None:
            continue
        service_soup = BeautifulSoup(service_xml, "lxml")

        """
        <landing-page>
            <title>Amazon Elastic Compute Cloud Documentation</title>
            <titleabbrev>Amazon EC2</titleabbrev>
            <abstract>Amazon Elastic Compute Cloud (Amazon EC2) is a [...]</abstract>
            [...]
            <main-area>
                <sections>
                    <section id="amazon-ec2">
                        <title>Amazon EC2</title>
                        <tiles>
                        <tile href="/AWSEC2/latest/UserGuide/">
                            <title>User Guide for Linux Instances</title>
                            <abstract> Describes key [...]</abstract>
                            <more-links/>
                        </tile>
                    </section>
                    [...]
                </sections>
            </main-area>
            [...]
        </landing-page>
        """

        # Service name
        # Page title is "<product> Documentation", remove " Documentation"
        page_title = service_soup.find("landing-page").title.string
        service_name = re.sub(r" Documentation$", "", page_title)
        service["name"] = service_name

        # Service blurb
        # Remove extra newlines found in the XML
        # Some landing pages don't have descriptions
        service_blurb = service_soup.find("landing-page").abstract.string
        try:
            # 'blurb' obtained from HTML can have weird encoding
            # fix: https://stackoverflow.com/a/66815577
            bytes_blurb = bytes(service["blurb"], encoding="raw_unicode_escape")
            service["blurb"] = bytes_blurb.decode("utf-8", "strict")
            service["blurb"] = " ".join(service_blurb.split())
        except:
            service["blurb"] = ""

        # Service abbreviation (e.g. 'Amazon EC2')
        service["abbreviation"] = service_soup.find("landing-page").titleabbrev.string

        # <section> names often contain extra AWS product names!
        # Only if they start with "AWS", "Amazon"
        # e.g. AWS Lambda Data Firehose
        sections = service_soup.find_all("section")
        try:
            # Get section
            sections_titles = [sec.title.text for sec in sections]

            # Clean whitespace
            " ".join(sections_titles.split())

            # Filter
            sections_titles = [
                st
                for st in sections
                if st.startswith("AWS")
                or st.startswith("Amazon")
                or st.endswith("Documentation")
                or st.endswith("User Guide")
                and len(st.text) > 0
            ]
        except:
            sections_titles = []

        print(f"    Extra (section names): {sections_titles}")
        extra_names += sections_titles

        # Dig into the first link of the page to get more content
        # (typically a 'User Guide' or 'Developer pythonGuide')
        # Not all sections have hrefs. Get the first one that does.
        service_hrefs = service_soup.find_all("tile")
        for sh in service_hrefs:
            try:
                service_first_href = sh["href"]
                break
            except:
                continue

        # Discard URL parameters if they exist
        if "?" in service_first_href:
            service_first_href = service_first_href.split("?")[0]

        print(f"    Fetching {service_first_href}...")

        # Skip absolute product links (non-docs sites)
        if service_first_href.startswith("/"):
            # The page has no XML layout, it's pure HTML
            sleep(0.5)
            service_first_url = urllib.parse.urljoin(main_url, service_first_href)
            r = get(service_first_url)
            service_first_soup = BeautifulSoup(r.text, "html.parser")
        else:
            # Hack-ish way to set the result to nothing, so the next steps will skip
            # but the product will still get added to the dict.
            service_first_soup = BeautifulSoup("", "html.parser")

        # The page can sometimes be a placeholder with a redirect:
        # The last index.html will be replaced by the page in <meta http-equiv="refresh">
        # as in: <meta http-equiv="refresh" content="10;URL=concepts.html"
        # e.g. https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/index.html to:
        #      https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/concepts.html
        meta_refresh = service_first_soup.find("meta", attrs={"http-equiv": "refresh"})
        if meta_refresh:
            index = meta_refresh["content"].split("=")[1]

            # Re-request the above with the right redirected URL

            if service_first_url.endswith("/"):
                # e.g. "https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/"
                # Just add the new index
                service_first_url = service_first_url + index
            else:
                # e.g.  "https://docs.aws.amazon.com/sagemaker/latest/dg/what-is.htm"
                # replace the last page of the path.
                service_first_url = re.sub(r"([^/]+)$", index, service_first_url)

            sleep(0.5)
            r = get(service_first_url)
            service_first_soup = BeautifulSoup(r.text, "html.parser")

        # Get the first <p>. If it's too short, get the next and so on
        paragraphs = service_first_soup.find_all("p")
        for p in paragraphs:
            clean_p = " ".join(p.text.split())
            if len(clean_p) < 100:
                continue
            else:
                # 'desc' obtained from HTML can have weird encoding
                # fix: https://stackoverflow.com/a/66815577
                bytes_desc = bytes(clean_p, encoding="raw_unicode_escape")
                service["desc"] = bytes_desc.decode("utf-8", "strict")
                break

        # <dt> elements often contain extra AWS product names!
        # Only if they start with "AWS", "Amazon" or the product name itself
        # (from the main page, w/o a brand prefix, e.g. "SageMaker")
        dts = service_first_soup.find_all("dt")
        dts_list = [
            dt.text
            for dt in dts
            if dt.text.startswith("AWS")
            or dt.text.startswith("Amazon")
            or dt.text.startswith(name)
            and not len(dt.text.split()) > 4
        ]

        # Clean
        dts_list = [" ".join(dt.split()) for dt in dts_list]

        print(f"    Extra (terms): {dts_list}")
        extra_names += dts_list

        names.append(name)
        items.append(service)

    # Add the 'extra_names' to as new product entries (name only)
    existing_names = [i["name"] for i in items]
    extra_names = list(set(list(extra_names)))

    for en in extra_names:
        # Clean
        en = " ".join(en.split())
        if en in existing_names:
            continue
        else:
            service = {"name": en, "blurb": "", "abbreviation": "", "desc": ""}
            items.append(service)

    return items


def get_page_xml(url) -> str:
    r = get(url)
    soup = BeautifulSoup(r.text, "html.parser")

    script_tags = soup.select("script")
    for s in script_tags:
        if not s.string:
            continue

        match = re.search(
            r"landingPageXml = '(?P<encoded_xml>.+)';", s.string, re.M | re.I
        )

        if match:
            return unquote(match["encoded_xml"])

    return None


def save_items(items, filename) -> None:
    with open(filename, "w") as f:
        f.write(json.dumps(items, indent=2, separators=(",", ": "), ensure_ascii=False))


if __name__ == "__main__":
    # Usage python get.py <json to save>

    # items = get_items()
    items = get_docs_items()

    # import pprint
    # pprint.pprint(items)

    filename = sys.argv[1]

    save_items(items, filename)
