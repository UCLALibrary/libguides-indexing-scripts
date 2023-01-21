import csv
import re
import requests
import sys
import traceback
from bs4 import BeautifulSoup
from pathlib import Path
from typing import Any, List

from pprint import pprint  # for debugging


def get_guide_url_from_path(path: Path) -> str:
    """Convert path from harvested LibGuide to a URL.

    Example path: ../libguider/data/1221796/page-8937658.html
    Matching URL: https://guides.library.ucla.edu/c.php?g=1221796&p=8937658
    """
    # Look for 2 groups of digits, separated by "/page-"
    pattern = re.compile("([0-9]+)/page-([0-9]+)")
    match = re.search(pattern, str(path))
    if match and (len(match.groups()) == 2):
        m1 = match.group(1)
        m2 = match.group(2)
        return f"https://guides.library.ucla.edu/c.php?g={m1}&p={m2}"
    else:
        return None


def get_libguide_data(soup: BeautifulSoup) -> dict[str, Any]:
    """Return selected data from a LibGuide HTML document.

    If document does not have the wanted metadata, returns an empty dictionary.
    """
    data: dict = {}
    try:
        data["title"] = soup.find(name="meta", attrs={"name": "DC.Title"})["content"]
        data["creator"] = soup.find(name="meta", attrs={"name": "DC.Creator"})[
            "content"
        ]
        data["uri"] = soup.find(name="meta", attrs={"name": "DC.Identifier"})["content"]
        # Many duplicate links in some files, so dedup via set
        website_links = set()
        # Act only on links we care about
        # Find links to main website, not other related sites
        LINKS_TO_FIND = ["//library.ucla.edu", "//www.library.ucla.edu"]
        for link in soup.find_all("a", href=True):
            link_to_check = link["href"]
            for link_to_find in LINKS_TO_FIND:
                if link_to_find in link_to_check:
                    # Format links in a standard way
                    website_link = standardize_link(link_to_check)
                    website_links.add(website_link)
                    # print(website_link)
        data["links"] = website_links
    except TypeError:
        # Ignore these: HTML does not have content we want to index
        pass
    except Exception:
        # Unknown other errors; for now, print stack trace and crash.
        traceback.print_exc()
        raise
    return data


def standardize_link(link: str) -> str:
    # QAD application of standard format for deduplication
    # Could be https://, http://, or scheme-less like // - remove all for de-duping
    # Also strip terminal / if present.
    # Remove internal spaces, which are typos.
    link = link.replace(" ", "")
    patterns_to_replace = "https://?|http://?|^//?|/$"
    printable_link = re.sub(patterns_to_replace, "", link)
    # Remove embedded CR/LF
    printable_link = printable_link.replace("\r", "").replace("\n", "")
    # Change bare library.ucla.edu to www.library.ucla.edu
    if printable_link.startswith("library"):
        printable_link = "www." + printable_link
    # Finally, use consistent https scheme
    return "https://" + printable_link


def get_website_urls() -> dict:
    # Dictionary of all relevant libguides data, keyed on website url.
    # Each url will have a list of dicts of other libguides data,
    # for each page it's used in.
    website_urls: dict[str, List] = {}

    HTML_ROOT = "../libguider/data"
    pages = "**/page*.html"
    # 4 pages, for small tests
    # pages = "710903/page*.html"
    p = Path(HTML_ROOT)
    for html_file in sorted(p.glob(pages)):
        print(f"Checking {html_file}...")
        with open(html_file) as f:
            # html5lib gives better results than built-in html.parser
            soup = BeautifulSoup(f, "html5lib")
            libguide_data = get_libguide_data(soup)
            libguide_data["guide_url"] = get_guide_url_from_path(html_file)
            libguide_data["html_file"] = str(html_file)

        # Go through each page's unique library links, and
        # add data for each unique website url to dictionary.
        # Copy links, then delete from libguide_data - unneeded clutter.
        links = libguide_data.get("links")
        if links:
            del libguide_data["links"]
            for url in links:
                if website_urls.get(url):
                    website_urls[url].append(libguide_data)
                else:
                    website_urls[url] = [libguide_data]

    return website_urls


def get_redirect_data(redirect_filename: str) -> list:
    redirects: list = []
    with open(redirect_filename) as csv_file:
        reader = csv.DictReader(csv_file)
        for line in reader:
            redirects.append(line)
    # We need just the old website URL
    return [redirect["Custom field (URL)"] for redirect in redirects]


def write_missing_redirects(missing_redirects: list) -> None:
    column_headers = missing_redirects[0].keys()
    with open("missing_redirects.csv", "wt") as csv_file:
        writer = csv.DictWriter(csv_file, column_headers, dialect="excel")
        writer.writeheader()
        writer.writerows(missing_redirects)

    # Create summary file with urls and number of libguide pages using each
    urls = [redirect["website_url"] for redirect in missing_redirects]
    counts = {url: urls.count(url) for url in urls}
    summary = [{"website_url": k, "libguide_count": v} for (k, v) in counts.items()]
    column_headers = summary[0].keys()
    with open("missing_redirects_summary.csv", "wt") as csv_file:
        writer = csv.DictWriter(csv_file, column_headers, dialect="excel")
        writer.writeheader()
        writer.writerows(summary)


def main() -> None:
    redirect_filename = sys.argv[1]
    redirects = get_redirect_data(redirect_filename)
    website_urls = get_website_urls()

    # Compare each website url from libguides with redirects
    # and report on those which are not found.
    print(f"Checking redirects for {len(website_urls)} libguides website urls...")
    # Collect output data in missing_redirects
    missing_redirects: list = []
    for website_url in sorted(website_urls):
        if website_url in redirects:
            print(f"Found {website_url} - skipping")
            found = True
        else:
            # Some urls are redirected within Drupal, so if first check is not found,
            # get the final url and check it too.
            print(f"{website_url} not found, checking Drupal redirect...")
            found = False
            response = requests.get(website_url, allow_redirects=True)
            new_url = response.url
            status_code = response.status_code
            if new_url != website_url:
                if new_url in redirects:
                    print(f"Found Drupal redirect {new_url} - skipping")
                    found = True
                else:
                    print(f"{new_url} Drupal redirect also not found")
                    found = False
            else:
                # Clear new_url for simpler logs, since it's same as website_url
                new_url = ""
        if not found:
            print(f"Reporting {website_url}")
            libguide_pages: list = website_urls[website_url]
            for page in libguide_pages:
                missing_redirects.append(
                    {
                        "website_url": website_url,
                        "website_alias": new_url,
                        "status_code": status_code,
                        "libguide_url": page["guide_url"],
                        "creator": page["creator"],
                        "title": page["title"],
                    }
                )
        print()
    write_missing_redirects(missing_redirects)


if __name__ == "__main__":
    main()
