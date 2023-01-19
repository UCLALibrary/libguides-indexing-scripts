from elastic_lib_client import ElasticLibClient
import argparse
import api_keys


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i",
        "--index",
        help="Elasticsearch index to perform operations on",
        action="store",
        default="index",
    )
    parser.add_argument(
        "-u",
        "--base_url",
        help="Base url of Elasticsearch index to use",
        action="store",
        default="http://localhost:9200",
    )

    args = parser.parse_args()

    es = ElasticLibClient(
        index_name=args.index, base_url=args.base_url, base64_api_key=api_keys.API_KEY
    )

    # 4 pages, for small tests
    es.index_libguides(file_spec="710903/page*.html")
    # Or do a full test indexing of all pages
    # es.index_libguides()

    # For testing, since indexing can still be running when search is done
    es.ELASTIC_SEARCH.indices.refresh()
    document_count = es.ELASTIC_SEARCH.count()["count"]
    print(f"{document_count = }")

    resp = es.ELASTIC_SEARCH.search(query={"match_all": {}})
    print("Showing first (up to) 10 titles...")
    for hit in resp["hits"]["hits"]:
        print(hit["_source"]["title"])


if __name__ == "__main__":
    main()
