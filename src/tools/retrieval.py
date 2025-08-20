from clients.meilisearch import search_client
import json


async def search_movie_bm25(query: str) -> list:
    """Searches for movies based on a query using Meilisearch.


    To leverage this function, you should make sure the meilisearch server is up and running, and instantiate the movie collection from seed.

    Args:
        query (str): The search query to describe the movie you are looking for.

    Returns:
        list: A list of movie results from Meilisearch.
    """

    results = search_client.index("movies").search(query, opt_params={"limit": 20})

    return json.dumps(results["hits"])
