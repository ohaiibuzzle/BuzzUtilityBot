from bs4 import BeautifulSoup
import discord 
import requests
import random
import string

from tf_image_processor.tf_process import process_url

global random_gen
random_gen = random.SystemRandom()
endpoint = 'https://safebooru.org/index.php?page=dapi&s=post&q=index&tags=rating:safe '

def tf_scan(url:str):
    try:
        res = process_url(url)
    except ValueError:
        return True
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

def get_image(tags:str, position: int, bypass=False):
    soup = BeautifulSoup(requests.get(endpoint + tags).text, "lxml")
    count = soup.find_all('post').__len__()
    try:
        if position > count:
            position = random_gen.randint(0, count - 1)
    except ValueError:
        return None
    try:
        for _ in range(3):            
            post = soup.find_all('post')[position]
            #print(position)
            
            if not bypass:
                if not tf_scan(post.get('file_url')):
                    continue
            
            embed = discord.Embed(title="Your random image!")
            embed.set_image(url = post.get('file_url'))
            embed.add_field(
                name='Source',
                value=post.get('source'),
                inline=False
            )
            
            embed.add_field(
                name='Tags',
                value = '```\n'+post.get('tags').strip()+'\n```',
                inline = False
            )
            
            return embed
        return None
    except IndexError:
        return None

def convert_to_sb_tag(tags: str):
    new_tags = []
    for tag in tags:
        tag = tag.lower().strip()
        tag = tag.replace(" ", '_')
        new_tags.append(tag)
    ret = ' '.join(new_tags)
    #print(ret)
    return ret

def safebooru_random_img(tags: str, ch):
    global random_gen
    random_gen = random.SystemRandom()
    tags = convert_to_sb_tag(tags)

    if ch.type is not discord.ChannelType.private:
        emb = get_image(tags, random_gen.randint(0,99), ch.is_nsfw())
    else:
        emb = get_image(tags, random_gen.randint(0,99), True)
    if emb:
        return emb
    else:
        return None
    
if __name__ == "__main__":
    arg = 'Ganyu (Genshin Impact) + Amber (Genshin Impact)'
    args = arg.split('+')
    
    #print(safebooru_random_img(args).to_dict(), discord.ext.commands.Context())
    pass