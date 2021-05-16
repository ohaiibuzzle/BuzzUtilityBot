from bs4 import BeautifulSoup
import discord 
import requests
import random
import string

global random_gen
random_gen = random.SystemRandom()
endpoint = 'https://safebooru.org/index.php?page=dapi&s=post&q=index&tags=rating:safe '

def get_image(tags:str, position: int):
    soup = BeautifulSoup(requests.get(endpoint + tags).text, "lxml")
    count = soup.find_all('post').__len__()
    try:
        if position > count:
            position = random_gen.randint(0, count - 1)
    except ValueError:
        return None
    try:
        post = soup.find_all('post')[position]
        #print(position)
        
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

def random_image(tags: str):
    global random_gen
    random_gen = random.SystemRandom()
    tags = convert_to_sb_tag(tags)
    emb = get_image(tags, random_gen.randint(0,99))
    if emb:
        return emb
    else:
        return None
    
if __name__ == "__main__":
    arg = 'Ganyu (Genshin Impact) + Amber (Genshin Impact)'
    args = arg.split('+')
    
    print(random_image(args).to_dict())
    pass