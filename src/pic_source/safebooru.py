from bs4 import BeautifulSoup
import discord 
import requests
import random
import string
import asyncio
import aiohttp

from tf_image_processor.tf_process import async_process_url

random_gen = random.SystemRandom()
endpoint = 'https://safebooru.org/index.php?page=dapi&s=post&q=index&tags=rating:safe '

async def tf_scan(url:str) -> discord.Embed:
    """
    Use TensorFlow to scan the image against an ML model.
    Warning: If TF fails, it is ignored, so make sure either the tag filter is on or you may end up with things in your SFW channels
    :param url: an URL to scan
    """
    try:
        res = await async_process_url(url)
    except ValueError:
        return True
    print(res)
    if res['(o-_-o) (H)'][0] >= 0.45:
        print('AI test failed with H content')
        return False
    if res['(╬ Ò﹏Ó) (P)'][0] >= 0.5:
        print('AI test failed with P content')
        return False
    if res['(°ㅂ°╬) (S)'][0] >= 0.5:
        print('AI test failed with S content')
        return False
    return True

async def get_image(tags:str, bypass=False):
    """
    Search SafeBooru for images
    :param bypass: Bypass filters
    :param query: What to look for
    """
    global random_gen
    
    timeout = aiohttp.ClientTimeout(total=15)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        res = await session.get(endpoint + tags)
    
        soup = BeautifulSoup(await res.read(), "lxml")
        count = int(soup.find('posts')['count'])
        
        #print(endpoint + tags)
        #print(count)
        try:
            position = random_gen.randint(0, count - 1)
        except ValueError:
            return None
        for _ in range(3):   
            if position < 100:
                try:         
                    post = soup.find_all('post')[position]
                    #print(position)
                    
                    if not bypass:
                        if not (await tf_scan(post.get('file_url'))):
                            position = random_gen.randint(0, count - 1)
                            continue
                    
                    embed = discord.Embed(title="Your random image!")
                    embed.set_image(url = post.get('file_url'))
                    embed.add_field(
                        name='Source',
                        value=post.get('source') + ' ',
                        inline=False
                    )
                    
                    embed.add_field(
                        name='Tags',
                        value = '```\n'+post.get('tags').strip()[:1018]+'\n```',
                        inline = False
                    )
                    
                    return embed
                except IndexError:
                    return None
            else:
                page = int(position / 100)
                
                remote_res = await session.get(endpoint + tags + '&pid=' + str(page))
                
                remote_soup = BeautifulSoup(await remote_res.read(), "lxml")
                
                position = position % 100 - 1
                
                if position < 0:
                    position = 0
                
                post = remote_soup.find_all('post')[position]
                
                #print(page)
                #print(position)
                
                if not bypass:
                    if not (await tf_scan(post.get('file_url'))):
                        position = random_gen.randint(0, count - 1)
                        continue
                
                embed = discord.Embed(title="Your random image!")
                embed.set_image(url = post.get('file_url'))
                embed.add_field(
                    name='Source',
                    value=post.get('source') + ' ',
                    inline=False
                )
                
                embed.add_field(
                    name='Tags',
                    value = '```\n'+post.get('tags').strip()[:1018]+'\n```',
                    inline = False
                )
                
                return embed
        return None

def convert_to_sb_tag(tags: list):
    """
    Convert a string to safebooru compatible tags
    :param tags: a list of tags
    :return: A string of safebooru tags
    """
    new_tags = []
    for tag in tags:
        tag = tag.lower().strip()
        tag = tag.replace(" ", '_')
        new_tags.append(tag)
    ret = ' '.join(new_tags)
    #print(ret)
    return ret

async def safebooru_random_img(tags: list, ch) -> discord.Embed:
    """
    Randomly get an image from specified tags
    :param tags: A list of tags
    :param ch: The Discord channel (So we can decide if it's SFW)
    :return: An embed ready to be sent
    """
    tags = convert_to_sb_tag(tags)

    if ch.type is not discord.ChannelType.private:
        emb = await get_image(tags, ch.is_nsfw())
    else:
        emb = await get_image(tags, True)
    if emb:
        return emb
    else:
        return None
    
if __name__ == "__main__":
    arg = 'Ganyu (Genshin Impact) + Amber (Genshin Impact)'
    args = arg.split('+')
    
    #print(safebooru_random_img(args).to_dict(), discord.ext.commands.Context())
    pass