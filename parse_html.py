import re
import traceback
from bs4 import BeautifulSoup
from pathlib import Path
from typing import Any

# To view data while testing
from pprint import pprint


def get_data(soup: BeautifulSoup) -> dict[str, Any]:
    """Return selected data from a LibGuide HTML document.

    If document does not have the wanted metadata, returns an empty dictionary.
    """
    data: dict = {}
    try:
        data["title"] = soup.find(name="meta", attrs={"name": "DC.Title"})["content"]
        data["creator"] = soup.find(name="meta", attrs={"name": "DC.Creator"})[
            "content"
        ]
        data["description"] = soup.find(name="meta", attrs={"name": "DC.Description"})[
            "content"
        ]
        data["url"] = soup.find(name="meta", attrs={"name": "DC.Identifier"})["content"]
        data["text"] = [str for str in soup.body.stripped_strings]
    except TypeError:
        # Ignore these: HTML does not have content we want to index
        pass
    except Exception:
        # Unknown other errors; for now, print stack trace and crash.
        traceback.print_exc()
        raise
    return data


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


def main() -> None:
    # Specific guide (with subpages) for testing
    # HTML_ROOT = "../libguider/data/180388"
    # One specific guide/subpage for testing
    # pages = "page-1185902.html"

    # All guides
    HTML_ROOT = "../libguider/data"
    pages = "**/page*.html"

    p = Path(HTML_ROOT)
    for html_file in sorted(p.glob(pages)):
        with open(html_file) as f:
            # html5lib gives better results than built-in html.parser
            soup = BeautifulSoup(f, "html5lib")
            data = get_data(soup)
            if data:
                # TODO: Feed this to indexed
                # pprint(data, width=120)
                pass
            else:
                # TODO: Log this?
                guide_url = get_guide_url_from_path(html_file)
                print(f"No usable content in {html_file}: see {guide_url}")


if __name__ == "__main__":
    main()
