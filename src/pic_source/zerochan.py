import requests
import re
from time import sleep
from bs4 import BeautifulSoup
from random import SystemRandom, random
from discord import Embed, ChannelType

from tf_image_processor.tf_process import process_url

global random_gen
random_gen = SystemRandom()

pls_no_tags = ['Nipples'] #The AI *should* handle these, 'Bend Over', 'Panties', 'Bra', 'Underwear', 'Lingerie']

def tf_scan(url:str):
    try:
        res = process_url(url)
    except ValueError:
        print("AI Error")
        return True
    
    print(res)
    if res['(o-_-o) (H)'][0] >= 0.60:
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
                    

def search_zerochan(bypass, query: str):
    print(query)
    is_tag = True
    random_gen = SystemRandom()
    target = 'https://zerochan.net/search?q='
    tag_target = 'https://zerochan.net/'
    xml_specifier='?xml'
    pagination='&p='
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:78.0) Gecko/20100101 Firefox/78.0',
        'referer':'https://www.zerochan.net/'
    }

    res = requests.get(tag_target+query+xml_specifier, headers=headers, timeout=15)
    
    url = ''
    
    if not '?xml' in res.url: #Hit a tag
        is_tag = True
        soup = BeautifulSoup(requests.get(res.url+xml_specifier, headers=headers, timeout=15).content, features='lxml')
        url = res.url+xml_specifier
        query = res.url.split('/')[-1].replace('+', ' ')
        #print(query)
    elif 'application/rss+xml' in str(res.content):
        is_tag = True
        soup = BeautifulSoup(res.content, features = 'lxml')
        url = res.url
    else:
        soup = BeautifulSoup(requests.get(target+query+'&xml', headers=headers, timeout=15).content, features='lxml')
        url = target+query+'&xml'
        is_tag = False
        #sleep(0.5)
    
    #print(url)
    #print(is_tag)
    
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
                    
                    if not tf_scan(item.find('media:thumbnail')['url']):
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
                page_soup = BeautifulSoup(requests.get(tag_target+query+'?xml'+pagination+str(page), timeout=15).content, features='lxml')
                
                if 'Some content is for members only, please' in page_soup.text:
                    continue
                
                c = choice % (page_soup.find_all('item').__len__())
                if c < 0:
                    c = 0
                    
                try:
                    item = page_soup.find_all('item')[c]
                except ZeroDivisionError:
                    return None
                
                if not bypass:
                    kw = item.find('media:keywords').text.strip()
                    
                    if not kw_filter(kw):
                        continue
                    if not tf_scan(item.find('media:thumbnail')['url']):
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
                if not tf_scan(item.find('media:thumbnail')['url']):
                        continue

            #print(item)

            return {
                'link': item.find('guid').text,
                'title': item.find('media:title').text,
                'thumbnail': item.find('media:thumbnail')['url'],
                'content': item.find('media:content')['url'],
                'keywords': item.find('media:keywords').text.replace(chr(0x09), '').replace('\r\n', ' ').strip()
            }

def construct_zerochan_embed(ch, query: str):
    if ch.type is not ChannelType.private:
        res = search_zerochan(ch.is_nsfw(), query)
    else: 
        res = search_zerochan(True, query)
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
    res = search_zerochan(False, 'Tatsumaki')

    if res != None:
        print(res)
    else:
        print('NSFW or forbidden tag!')