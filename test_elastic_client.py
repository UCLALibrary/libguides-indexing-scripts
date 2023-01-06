from elastic_lib_client import ElasticLibClient


def main():
    es = ElasticLibClient("http://localhost:9200")
    es.index_libguides()
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
