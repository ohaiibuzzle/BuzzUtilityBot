import json
import asyncio
import aiohttp
import random

global_random = random.SystemRandom()

async def search_danbooru(query:str) -> dict:
    timeout = aiohttp.ClientTimeout(total=15)
    async with aiohttp.ClientSession(timeout=timeout) as client:
        res_tag_search = await client.get(f'https://danbooru.donmai.us/tags.json?search[name_or_alias_matches]={query}')
        result_json = await res_tag_search.json()
        tag = result_json[0]['name']
        choice =  global_random.choice(range(result_json[0]['post_count']))
        page = choice // 100
        choice = choice % 100
        res = await client.get(f'https://danbooru.donmai.us/posts.json?tags={tag}&limit=100&page={page}')
        res_chosen = (await res.json())[choice]
        return res_chosen


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    print(loop.run_until_complete(search_danbooru('hu tao')))