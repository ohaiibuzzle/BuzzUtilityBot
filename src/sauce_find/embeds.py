from saucenao_api import BasicSauce
from sauce_find.saucenao import find_sauce
import json
import discord 
import pixivpy3 

image_format = ['.jpg', '.JPG',
                '.png', '.PNG',
                '.gif']

def construct_saucenao_embed_pixiv(attachment: BasicSauce):
    
    client = pixivpy3.AppPixivAPI()

    with open('pixiv.key', 'r') as pixivkey:
        client.auth(refresh_token=pixivkey.readline())
    
    raw_json = attachment.raw
    #print(raw_json)
    
    illust = client.illust_detail(raw_json['data']['pixiv_id']).illust
    #print(illust)

    embed = discord.Embed(title='Sauce found!')
    embed.type = 'rich'
    embed.url = attachment.urls[0]
    
    embed.set_thumbnail(url=attachment.thumbnail)
    
    embed.add_field(
        name = 'Title',
        value = illust.title,
        inline = False
    )
    
    embed.add_field(
        name = 'Type',
        value = illust.type.capitalize(),
        inline = False
    )
    
    embed.add_field(
        name = 'Similarity',
        value = str(attachment.similarity) + "%",
        inline = False
    )
    
    embed.add_field (
        name = 'Author',
        value = "{}, Pixiv ID: {}".format(illust.user.name, illust.user.id),
        inline = False
    )
    
    tag_str = ''
    if illust.tags.__len__() > 0 :
        for tag in illust.tags:
            if tag.translated_name != None:
                tag_str += tag.translated_name
                tag_str += ', '
            else:
                tag_str += tag.name
                tag_str += ', '
        tag_str = tag_str[:-2]
    else:
        tag_str = None
    
    embed.add_field (
        name = 'Tags',
        value = tag_str,
        inline = False
    )
    
    embed.set_footer(
        icon_url='https://policies.pixiv.net/pixiv.a2954ee2.png',
        text = 'Pixiv'
    )
    
    return embed


if __name__ == '__main__':
    print(construct_saucenao_embed_pixiv(find_sauce('https://i.pximg.net/img-master/img/2021/04/21/18/00/47/89297449_p0_master1200.jpg')))