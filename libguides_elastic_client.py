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
    parser.add_argument(
        "-f",
        "--file_spec",
        help="Files to index (default: all files)",
        action="store",
        default="**/page*.html",
    )

    args = parser.parse_args()

    """ IMPORTANT:
        The Elasticsearch API client, by default, acts on *all* indexes the API_KEY
        can access.  There's no native way to set a single default index.
        All uses of es.ELASTIC_SEARCH need to specify (index=es.INDEX).
    """
    es = ElasticLibClient(
        index_name=args.index, base_url=args.base_url, base64_api_key=api_keys.API_KEY
    )

    # Delete all documents from index before indexing current content.
    # delete_by_query() requires body param, not straight query like search().
    resp = es.ELASTIC_SEARCH.delete_by_query(
        index=es.INDEX,
        conflicts="proceed",
        refresh=True,
        wait_for_completion=True,
        body={"query": {"match_all": {}}},
    )
    print(f"Deleted {resp['deleted']} of {resp['total']} documents")

    # Do a full indexing of all pages
    es.index_libguides(file_spec=args.file_spec)
    # 4 pages, for small tests
    # es.index_libguides(file_spec="710903/page*.html")

    # Force a refresh, since indexing can still be running when search is done
    es.ELASTIC_SEARCH.indices.refresh(index=es.INDEX)
    # How many documents are currently indexed?
    document_count = es.ELASTIC_SEARCH.count(index=es.INDEX)["count"]
    print(f"{document_count = }")
    # Show a few sample titles
    resp = es.ELASTIC_SEARCH.search(index=es.INDEX, query={"match_all": {}})
    print("Showing first (up to) 10 titles...")
    for hit in resp["hits"]["hits"]:
        print(hit["_source"]["title"])


if __name__ == "__main__":
    main()
