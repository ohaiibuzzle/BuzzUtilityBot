import asyncio
import random

import aiohttp


async def search_danbooru(query: str) -> dict:
    """
    Search Danbooru for images
    :param query: The query string
    :return: a dictionary of the image chosen
    """
    timeout = aiohttp.ClientTimeout(total=15)
    async with aiohttp.ClientSession(timeout=timeout) as client:
        # Convert spaces into underscores
        query = query.replace(" ", "_")

        res_tag_search = await client.get(
            f"https://danbooru.donmai.us/tags.json?search[fuzzy_name_matches]={query}&search[hide_empty]=1"
        )
        result_json = await res_tag_search.json()
        tag = result_json[0]["name"]
        # we cannot go above page 1000, so that limits the max choice to 1000*100 = 100000
        post_count = min(result_json[0]["post_count"], 100000)
        choice = random.randint(0, post_count)
        page = choice // 100
        choice = choice % 100
        res = await client.get(
            f"https://danbooru.donmai.us/posts.json?tags={tag}&limit=100&page={page}"
        )
        res_chosen = (await res.json())[choice]
        return res_chosen


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    print(loop.run_until_complete(search_danbooru("hu tao")))
