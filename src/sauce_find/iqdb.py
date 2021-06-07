import aiohttp, asyncio
import discord
from bs4 import BeautifulSoup

iqdb_endpoint = 'https://iqdb.org/?url='

async def get_sauce(url: str):
    
    timeout = aiohttp.ClientTimeout(total=15)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        res = await session.get(iqdb_endpoint+url)
        soup = BeautifulSoup(res.read(), 'html.parser')
        
        result_disp = soup.find('div', id='pages')
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

async def construct_iqdb_embed(url: str):
    data = await get_sauce(url)
    if not data:
        return None
    embed = discord.Embed(title='Sauce found!')
    embed.url = data['link']
    embed.set_thumbnail(url=data['thumbnail'])
    embed.add_field(
        name='Location',
        value=data['link'],
        inline=False
    )
    
    embed.add_field(
        name='Alt Text',
        value=data['alt_text'],
        inline=False
    )
    return embed

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    res = loop.run_until_complete(construct_iqdb_embed('https://media.discordapp.net/attachments/807429230874722309/840291361931919360/874fdf4ac200e7fc4d89ba98e119f726.jpg'))
    print(res.to_dict())
    pass