from elastic_lib_client import ElasticLibClient


def main():
    es = ElasticLibClient("http://localhost:9200")
    es.index_libguides()
    resp = es.ELASTIC_SEARCH.search(query={"match_all": {}})
    for hit in resp["hits"]["hits"]:
        print(hit["_source"]["title"])


if __name__ == "__main__":
    main()
