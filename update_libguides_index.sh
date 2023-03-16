#!/bin/bash

source ./libguides_secrets.cfg

# Run libguider to download current guides as HTML files
echo "Downloading latest LibGuides HTML files into ${LIBGUIDER_DIR}/data..."
cd ${LIBGUIDER_DIR}
pipenv run python libguider.py --site_id ${LIBGUIDER_SITE} --api_key ${LIBGUIDER_API_KEY}

# Run indexing program
echo "Indexing LibGuides data..."
cd ${LIBGUIDES_INDEX_DIR}
pipenv run python libguides_elastic_client.py -u ${LIBGUIDES_TARGET} -i ${LIBGUIDES_INDEX_TEST}
