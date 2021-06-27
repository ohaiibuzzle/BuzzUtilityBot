import asyncio
import re
from time import sleep
from bs4 import BeautifulSoup
from random import SystemRandom, random
from discord import Embed, ChannelType
import aiohttp

from tf_image_processor.tf_process import async_process_url


random_gen = SystemRandom()

pls_no_tags = ['Nipples'] #The AI *should* handle these, 'Bend Over', 'Panties', 'Bra', 'Underwear', 'Lingerie']

async def tf_scan(url:str):
    try:
        res = await async_process_url(url)
    except ValueError:
        print("AI Error")
        return True
    
    print(res)
    if res['(o-_-o) (H)'][0] >= 0.59:
        print('AI test failed with H content')
        return False
    if res['(╬ Ò﹏Ó) (P)'][0] >= 0.5:
        print('AI test failed with P content')
        return False
    if res['(°ㅂ°╬) (S)'][0] >= 0.5:
        print('AI test failed with S content')
        return False
    return True

def kw_filter(keywords: str):
    for x in pls_no_tags:
        if re.search(r"\b" + re.escape(x) + r"\b", keywords):
            print('Found banned tag: ' + x)
            return False
    return True
                    

async def search_zerochan(bypass, query: str):
    global random_gen
    print(query)
    is_tag = True
    target = 'https://zerochan.net/search?q='
    tag_target = 'https://zerochan.net/'
    xml_specifier='?xml&s=id'
    pagination='&p='
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:78.0) Gecko/20100101 Firefox/78.0',
        'referer':'https://www.zerochan.net/'
    }
    
    timeout = aiohttp.ClientTimeout(total=15)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        res = await session.get(tag_target+query+xml_specifier, headers=headers)
        
        #url = ''
    
        if not '?xml' in str(res.url): #Hit a tag
            is_tag = True
            res = await session.get(str(res.url)+xml_specifier, headers=headers)
            soup = BeautifulSoup(await res.read(), features='lxml')
            #url = res.url+xml_specifier
            query = str(res.url).split('/')[-1].replace('+', ' ')
            #print(query)
        elif 'application/rss+xml' in str(await res.read()):
            is_tag = True
            soup = BeautifulSoup(await res.read(), features = 'lxml')
            #url = res.url
        else:
            res = await session.get(target+query+'&xml&s=id', headers=headers)
            soup = BeautifulSoup(await res.read(), features='lxml')
            #url = target+query+'&xml'
            is_tag = False
            #sleep(0.5)
        
        #print(url)
        #print(is_tag)
        #print(soup)
        
        
        total_amount = 0
        item_amount = len(soup.find_all('item'))
        if item_amount == 0:
            #print(is_tag)
            #print(soup)
            return 'No result'

        #print(total_amount)
        #print(choice)
        if is_tag:
            try:
                total_amount = int(re.search(r'\d{1,3}(,\d{3})*(\.\d+)?', soup.find('description').text)[0].replace(',',''))
            except TypeError:
                total_amount = item_amount

            for _ in range(3):
                choice = random_gen.randint(0, total_amount-1)
                if choice < item_amount-1:
                    
                    if choice < 0:
                        choice = 0
                    item = soup.find_all('item')[choice]
                    
                    if not bypass:
                        kw = item.find('media:keywords').text.strip()
                        
                        if not kw_filter(kw):
                            continue
                        
                        if not (await tf_scan(item.find('media:thumbnail')['url'])):
                            continue
                        
                    #print(item)
                    
                    return {
                        'link': item.find('guid').text,
                        'title': item.find('media:title').text,
                        'thumbnail': item.find('media:thumbnail')['url'],
                        'content': item.find('media:content')['url'],
                        'keywords': item.find('media:keywords').text.replace(chr(0x09), '').replace('\r\n', ' ').strip()
                    }

                else:
                    page = int(choice / (item_amount))+1
                    res = await session.get(tag_target+query+'?xml&s=id'+pagination+str(page))
                    page_soup = BeautifulSoup(await res.read(), features='lxml')
                    
                    if 'Some content is for members only, please' in page_soup.text:
                        continue
                    
                    c = choice % (page_soup.find_all('item').__len__())
                    if c < 0:
                        c = 0
                        
                    try:
                        item = page_soup.find_all('item')[c]
                    except ZeroDivisionError:
                        print(page_soup)
                        return None
                    
                    if not bypass:
                        kw = item.find('media:keywords').text.strip()
                        
                        if not kw_filter(kw):
                            continue
                        if not (await tf_scan(item.find('media:thumbnail')['url'])):
                            continue
                    
                    #print(item)

                    return {
                        'link': item.find('guid').text,
                        'title': item.find('media:title').text,
                        'thumbnail': item.find('media:thumbnail')['url'],
                        'content': item.find('media:content')['url'],
                        'keywords': item.find('media:keywords').text.replace(chr(0x09), '').replace('\r\n', ' ').strip()
                    }
        else:
            for _ in range(3):
                
                c = random_gen.randint(0, item_amount-1)
                item = soup.find_all('item')[c]
                
                if not bypass:
                    kw = item.find('media:keywords').text.strip()
                    
                    if not kw_filter(kw):
                        continue
                    if not await (tf_scan(item.find('media:thumbnail')['url'])):
                            continue

                #print(item)

                return {
                    'link': item.find('guid').text,
                    'title': item.find('media:title').text,
                    'thumbnail': item.find('media:thumbnail')['url'],
                    'content': item.find('media:content')['url'],
                    'keywords': item.find('media:keywords').text.replace(chr(0x09), '').replace('\r\n', ' ').strip()
                }

async def construct_zerochan_embed(ch, query: str):
    if ch.type is not ChannelType.private:
        res = await search_zerochan(ch.is_nsfw(), query)
    else: 
        res = await search_zerochan(True, query)
    if res == None:
        return None
    else:
        embed = Embed(title=res['title'])
        embed.url = res['link']
        embed.set_image(url=res['content'])
        
        embed.add_field(
            name = 'Source',
            value = embed.url,
            inline= False
        )
        embed.add_field(
            name = 'Tags',
            value = '```\n' + res['keywords'][:1018] + '\n```',
            inline = False
        )
        return embed
        
    
if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    res = loop.run_until_complete(search_zerochan(True, 'Ganyu'))

    if res != None:
        print(res)
    else:
        print('NSFW or forbidden tag!')