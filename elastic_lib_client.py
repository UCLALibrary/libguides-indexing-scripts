from elasticsearch import Elasticsearch
import json
import re
import traceback
from bs4 import BeautifulSoup
from pathlib import Path
from typing import Any


class ElasticLibClient:
    def __init__(
        self, base_url: str, index_name: str = "index", base64_api_key: str = ""
    ) -> None:
        self.INDEX = index_name
        self.ELASTIC_SEARCH = Elasticsearch(base_url, api_key=base64_api_key)

    def send_libguide(self, libguide: dict):
        es_doc_json = self._create_es_document(libguide)
        self.ELASTIC_SEARCH.index(
            index=self.INDEX, document=es_doc_json, id=libguide["uri"]
        )

    def _create_es_document(self, document_data: dict):
        """Convenience function to convert dict to Elasticsearch friendly document

        Any default or common fields to all Elasticsearch docs can be added here.
        """
        # Add sectionHandle, to allow targeting of libguide content
        document_data["sectionHandle"] = "Libguide"
        # Remove creator, until name handling is improved
        document_data.pop("creator", None)
        return json.dumps(document_data)

    def index_libguides(
        self, html_root: str = "../libguider/data", file_spec: str = "**/page*.html"
    ):
        """Index HTML LibGuides previously downloaded (via libguider).

        Keyword arguments:
        html_root: Relative path to the directory containing files to index.
        file_spec: Pattern used to match files to index.
        Defaults will index all files downloaded by
        a parallel installation of https://github.com/UCLALibrary/libguider
        """
        p = Path(html_root)
        for html_file in sorted(p.glob(file_spec)):
            print(f"Indexing {html_file}")
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
            data["summary"] = soup.find(name="meta", attrs={"name": "DC.Description"})[
                "content"
            ]
            data["uri"] = soup.find(name="meta", attrs={"name": "DC.Identifier"})[
                "content"
            ]
            # Combine all "text" from HTML body into one big string.
            data["fullText"] = " ".join([str for str in soup.body.stripped_strings])

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
