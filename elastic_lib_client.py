from elasticsearch import Elasticsearch
import json
import re
import traceback
from bs4 import BeautifulSoup
from pathlib import Path
from typing import Any


class ElasticLibClient:
    def __init__(
        self,
        base_url: str,
        index_name: str = "index",
        api_val: str = "",
        user_id: str = "",
    ) -> None:
        self.INDEX = index_name
        self.ELASTIC_SEARCH = Elasticsearch(base_url, api_key=(user_id, api_val))

    def send_libguide(self, libguide: dict):
        libguide["text"] = " ".join(libguide["text"])

        es_doc_json = self._create_es_document(libguide)

        op = self.ELASTIC_SEARCH.index(index=self.INDEX, document=es_doc_json)

    def _create_es_document(self, document_data: dict):
        """Convenience function to convert dict to Elasticsearch friendly document

        Any default or common fields to all Elasticsearch docs can be added here.
        """
        document_data["section"] = "Libguide"

        return json.dumps(document_data)

    def index_libguides(self):
        HTML_ROOT = "../libguider/data"
        pages = "**/page*.html"

        p = Path(HTML_ROOT)
        for html_file in sorted(p.glob(pages)):
            with open(html_file) as f:
                # html5lib gives better results than built-in html.parser
                soup = BeautifulSoup(f, "html5lib")
                data = self.get_data(soup)

                if data:
                    self.send_libguide(data)

                else:
                    # TODO: Log this?
                    guide_url = self.get_guide_url_from_path(html_file)
                    print(f"No usable content in {html_file}: see {guide_url}")

    def get_data(self, soup: BeautifulSoup) -> dict[str, Any]:
        """Return selected data from a LibGuide HTML document.

        If document does not have the wanted metadata, returns an empty dictionary.
        """
        data: dict = {}
        try:
            data["title"] = soup.find(name="meta", attrs={"name": "DC.Title"})[
                "content"
            ]
            data["creator"] = soup.find(name="meta", attrs={"name": "DC.Creator"})[
                "content"
            ]
            data["description"] = soup.find(
                name="meta", attrs={"name": "DC.Description"}
            )["content"]
            data["url"] = soup.find(name="meta", attrs={"name": "DC.Identifier"})[
                "content"
            ]
            data["text"] = [str for str in soup.body.stripped_strings]
        except TypeError:
            # Ignore these: HTML does not have content we want to index
            pass
        except Exception:
            # Unknown other errors; for now, print stack trace and crash.
            traceback.print_exc()
            raise
        return data

    def get_guide_url_from_path(self, path: Path) -> str:
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

