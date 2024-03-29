#!/bin/bash

_show_usage() {
    echo "Usage: $0 TEST|STAGE|PROD"
    exit 1
}

# Get full absolute path to this running script.
SCRIPT_PATH=$(dirname $(realpath -s $0))
# Config file must be in same directory as this script.
source ${SCRIPT_PATH}/libguides_secrets.cfg

# Required command-line argument to set index
if [ -z "$1" ]; then
  _show_usage
else
  case $1 in
    TEST  ) LIBGUIDES_INDEX=${LIBGUIDES_INDEX_TEST} ;;
    STAGE ) LIBGUIDES_INDEX=${LIBGUIDES_INDEX_STAGE} ;;
    PROD ) LIBGUIDES_INDEX=${LIBGUIDES_INDEX_PROD} ;;
  * ) _show_usage ;;
  esac
fi

# Run libguider to download current guides as HTML files
echo "Downloading latest LibGuides HTML files into ${LIBGUIDER_DIR}/data..."
cd ${LIBGUIDER_DIR}
# Delete previous documents before doing a full fresh harvest;
# otherwise, documents which no longer exist on LibGuides are never removed.
rm -rf data/*
# Make sure virtualenv is up to date first
pipenv sync
pipenv run python libguider.py --site_id ${LIBGUIDER_SITE} --api_key ${LIBGUIDER_API_KEY}

# Run indexing program
echo "Indexing LibGuides data into ${LIBGUIDES_INDEX}"
cd ${LIBGUIDES_INDEX_DIR}
# Make sure virtualenv is up to date first
pipenv sync
pipenv run python libguides_elastic_client.py -u ${LIBGUIDES_TARGET} -i ${LIBGUIDES_INDEX}
