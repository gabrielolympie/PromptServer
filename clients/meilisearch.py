import meilisearch
import os

MEILI_HTTP_ADDR = os.environ["MEILI_HTTP_ADDR"]

if "localhost" in MEILI_HTTP_ADDR:
    url = "http://" + MEILI_HTTP_ADDR
else:
    # https
    url = "https://" + MEILI_HTTP_ADDR

search_client = meilisearch.Client(url, os.environ["MEILI_MASTER_KEY"])
