import pixivpy3
import datetime 
import random
import discord
import io
import requests
import re

random_source = random.SystemRandom()

def px_getamount(query: str):
    #https://www.pixiv.net/ajax/search/artworks/hu%20tao?word=hu tao&order=date_d&mode=all&p=1&s_mode=s_tag&type=all&lang=en
    data = requests.get('https://www.pixiv.net/ajax/search/artworks/' + query + '?s_mode=s_tag&type=all&lang=en', timeout=10).json()
    return data['body']['illustManga']['total']

def get_image(query: str, bypass=False):
    #print(query)
    try:
        total = px_getamount(query)
    except TimeoutError:
        total = 30
        
    if total > 5000:
        total = 5000
                
    global random_source
    random_source = random.SystemRandom()
    client = pixivpy3.AppPixivAPI()
    
    with open('runtime/pixiv.key', 'r') as keyfile:
        client.auth(refresh_token=keyfile.readline())
        
    #print(total)
    for _ in range(3):
        choice = random_source.randrange(total) - 1
        
        if choice < 0:
            choice = 0
        
        result = client.search_illust(query, offset=choice)['illusts'][0]
        
        if not bypass:
            if result['restrict'] != 0:
                continue
        #print(choice)
        image_data = io.BytesIO(client.requests_call('GET', result['image_urls']['large'], 
                                                     headers={'Referer': 'https://app-api.pixiv.net/'}, stream=True).content)
        return result, image_data
    
    return None
    
def get_image_by_id(illust_id: int):
    client = pixivpy3.AppPixivAPI()
    
    with open('runtime/pixiv.key', 'r') as keyfile:
        client.auth(refresh_token=keyfile.readline())
        
    res = client.illust_detail(illust_id)['illust']
    
    if res['restrict'] != 0:
        return None
    
    image_data = io.BytesIO(client.requests_call('GET', res['image_urls']['large'], 
                            headers={'Referer': 'https://app-api.pixiv.net/'}, stream=True).content)
    
    embed = discord.Embed(title=res['title'], url="https://www.pixiv.net/en/artworks/" + str(res['id']))
    fn = res['image_urls']['large'].split('/')[-1]
    #print(fn)
    file = discord.File(image_data, filename=fn)
    embed.set_image(url='attachment://'+fn)
    
    embed.add_field(
        name = 'Title'+' ',
        value = res['title'],
        inline = False
    )
    
    embed.add_field (
        name = 'Author',
        value = "{}, Pixiv ID: {}".format(res['user']['name'], res['user']['id']),
        inline = False
    )
    
    tag_str = ''
    if res['tags'].__len__() > 0 :
        for tag in res['tags']:
            if tag.translated_name != None:
                tag_str += tag['translated_name']
                tag_str += ', '
            else:
                tag_str += tag['name']
                tag_str += ', '
        tag_str = tag_str[:-2]
    else:
        tag_str = None
    
    embed.add_field (
        name = 'Tags',
        value = tag_str,
        inline = False
    )
    return embed, file
    
    
def construct_pixiv_embed(query, channel):
    if channel.type == discord.ChannelType.private:
        res, img = get_image(query)
    else:
        res, img = get_image(query, channel.is_nsfw())
    if res != None:
        embed = discord.Embed(title=res['title'], url="https://www.pixiv.net/en/artworks/" + str(res['id']))
        fn = res['image_urls']['large'].split('/')[-1]
        #print(fn)
        file = discord.File(img, filename=fn)
        embed.set_image(url='attachment://'+fn)
        
        embed.add_field(
            name = 'Title'+' ',
            value = res['title'],
            inline = False
        )
        
        embed.add_field (
            name = 'Author',
            value = "{}, Pixiv ID: {}".format(res['user']['name'], res['user']['id']),
            inline = False
        )
        
        tag_str = ''
        if res['tags'].__len__() > 0 :
            for tag in res['tags']:
                if tag.translated_name != None:
                    tag_str += tag['translated_name']
                    tag_str += ', '
                else:
                    tag_str += tag['name']
                    tag_str += ', '
            tag_str = tag_str[:-2]
        else:
            tag_str = None
        
        embed.add_field (
            name = 'Tags',
            value = tag_str,
            inline = False
        )
        return embed, file
    return None

if __name__ == '__main__':
    print(get_image_by_id(re.findall(r'\d+','https://www.pixiv.net/en/artworks/85509963')[0]))