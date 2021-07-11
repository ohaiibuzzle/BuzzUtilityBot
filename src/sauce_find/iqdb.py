import aiohttp, asyncio
import discord
from bs4 import BeautifulSoup

iqdb_endpoint = 'https://iqdb.org/?url='

async def get_sauce(url: str):
    
    timeout = aiohttp.ClientTimeout(total=15)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        res = await session.get(iqdb_endpoint+url)
        soup = BeautifulSoup(await res.read(), 'html.parser')
        result_disp = soup.find('div', id='pages')
        print(result_disp)
        res = result_disp.find_all('table')
        res.remove(res[0])
        for _ in res:
            img_link = _.find('a')['href']
            if img_link.startswith('//'):
                img_link = 'https:' + img_link
            img_info = _.find('a').find('img')
            try:
                if 'Rating: s' not in img_info['alt']:
                    continue
            except TypeError:
                return None
            return {
                'link': img_link,
                'alt_text': img_info['alt'],
                'thumbnail': 'https://iqdb.org' + img_info['src']            
            } 
            #img_elem = _.find('a').find('img')
            #print(img_elem)
        
        return None
