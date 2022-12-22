# libguides-indexing-scripts
A collection of scripts related to harvesting and indexing LibGuides content at the UCLA Library

To confirm script is able to push Libguide content to an Elasticsearch instance:

Use [libguider harvester](https://github.com/tulibraries/libguider) to harvest a local copy of the libguides to index

Create a local Elasticsearch instance to connect to, a local Docker Elasticsearch cluster may be created with:
`docker run --rm -p 9200:9200 -p 9300:9300 -e "xpack.security.enabled=false" -e "discovery.type=single-node" docker.elastic.co/elasticsearch/elasticsearch:8.5.3`

`python test_elastic_client.py` will iterate through the downloaded libguides, push extracted content to the default index of the local Elasticsearch cluster and print the title of each libguide
