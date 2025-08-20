import sys

sys.path.append(".")

from tqdm.auto import tqdm
import pandas as pd
import os

from clients.meilisearch import search_client
from src.search.models.movie import Movie

## To define a seed, create a Model with methods options and post_init
seeds = {"movies": {"model": Movie, "seed": "movies.csv"}}

if __name__ == "__main__":

    for index, seed in seeds.items():
        print(f"***************** Indexing {index} *****************")

        ## First create the index
        search_client.create_index(index, options={"primaryKey": "id"})

        ## The update the options
        search_client.index(index).update_settings(seed["model"]().options())

        ## Then add the documents
        documents = pd.read_csv(os.path.join("src/search/seeds", seed["seed"]))
        documents.columns = documents.columns.str.lower()

        ## Convert to dict
        documents = documents.to_dict(orient="records")

        ## Wrap with object
        documents = [seed["model"](**document).__dict__ for document in tqdm(documents)]

        ## Add the documents to the index
        search_client.index(index).add_documents(documents)
