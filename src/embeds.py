from saucenao_api import BasicSauce
from saucenao import find_sauce
import json
import discord 
import pixivpy3 

image_format = ['.jpg', '.JPG',
                '.png', '.PNG',
                '.gif']

client = pixivpy3.AppPixivAPI()

with open('pixiv.key', 'r') as pixivkey:
    client.auth(refresh_token=pixivkey.readline())

def construct_saucenao_embed_pixiv(attachment: BasicSauce):
    
    raw_json = attachment.raw
    #print(raw_json)
    
    illust = client.illust_detail(raw_json['data']['pixiv_id']).illust
    print(illust)
    
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
    for tag in illust.tags:
        if tag.translated_name != None:
            tag_str += tag.translated_name
            tag_str += ', '
        else:
            tag_str += tag.name
            tag_str += ', '
    tag_str = tag_str[:-2]
    
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

def construct_save_embed_img(message: discord.Message):
    embed = discord.Embed(title = 'Saved!')
    
    embed.add_field(
        name = 'Fom',
        value = '@'+ message.author.name + '#' + message.author.discriminator +
        ' in #' + message.channel.name + ' on ' + message.channel.guild.name,
        inline = False
    )
    
    embed.add_field(
        name = 'Location',
        value = message.jump_url,
        inline = False
    )
    if message.content != '':
        embed.add_field(
            name = 'Content',
            value = message.content,
            inline = False
        )
    
    if (message.embeds.__len__() > 0):
        if (message.embeds[0].image):
            embed.set_image(url=message.embeds[0].image.proxy_url)
        elif (message.embeds[0].video):
            embed.set_image(url=message.embeds[0].video.url)
        elif (message.embeds[0].url.startswith('https://media.discordapp.net/attachments')) and (message.embeds[0].url[-4:] in image_format):
            embed.set_image(url=message.embeds[0].url)
        else:
            embedded_contents = ''
            for _ in message.embeds:
                embedded_contents += _.url
                embedded_contents += '\n'
            if (embedded_contents != ''):
                embed.add_field(
                    name='Embedded Content',
                    value = embedded_contents,
                    inline = False
                )

    if (message.attachments.__len__() > 0):
        att_contents = ''
        for _ in message.attachments:
            if _.content_type.startswith('image'):
                embed.set_image(url=_.url)
            else:
                embedded_contents += _.url
                embedded_contents += '\n'
        if att_contents != '':
            embed.add_field(
                name = 'Attached Content',
                value = att_contents,
                inline = False
            )
    return embed
    

if __name__ == '__main__':
    print(construct_saucenao_embed_pixiv(find_sauce('https://i.pximg.net/img-master/img/2021/04/21/18/00/47/89297449_p0_master1200.jpg')))