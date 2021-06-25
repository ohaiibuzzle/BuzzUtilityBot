import discord
from PIL import Image, ImageDraw, ImageFont, ImageOps
import requests
import io
    
IMAGE_FORMAT = ['.jpg', '.JPG',
                '.png', '.PNG',
                '.gif']

AVATAR_SIZE = 192

def construct_save_embed_img(message: discord.Message):
    embed = discord.Embed(title = 'Saved!')
    
    embed.add_field(
        name = 'From',
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
        elif (message.embeds[0].url.startswith('https://media.discordapp.net/attachments')) and (message.embeds[0].url[-4:] in IMAGE_FORMAT):
            embed.set_image(url=message.embeds[0].url)
        else:
            try:
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
            except UnboundLocalError:
                pass

    if (message.attachments.__len__() > 0):
        att_contents = ''
        for _ in message.attachments:
            if _.content_type.startswith('image'):
                embed.set_image(url=_.url)
            else:
                att_contents += _.url
                att_contents += '\n'
        if att_contents != '':
            embed.add_field(
                name = 'Attached Content',
                value = att_contents,
                inline = False
            )
    return embed
    
def construct_welcome_embed(member: discord.Member):    
    server_msg = "Welcome to " + member.guild.name + '!'
    member_msg = "@{}#{}".format(member.name, member.discriminator)
    
    background = Image.open('runtime/assets/bg.png', 'r').convert('RGBA')
    bg_w, bg_h = background.size

    print(member.avatar_url)
    icon = Image.open(requests.get(member.avatar_url, stream=True, timeout=15).raw, "r").convert('RGBA')
    icon = icon.resize((AVATAR_SIZE,AVATAR_SIZE))
    icon_w, icon_h = icon.size

    text_font = ImageFont.truetype("runtime/assets/font.ttf", 40)

    #mask pfp ->
    mask = Image.new('L', icon.size, 255)
    draw = ImageDraw.Draw(mask) 
    draw.ellipse((0, 0) + icon.size, fill=0)

    icon = ImageOps.fit(icon, mask.size, centering=(0.5, 0.5))
    icon.paste(0, (0,0), mask)
    offset = ((bg_w - icon_w)// 2, (bg_h-icon_h)//2)

    blurple = Image.new('RGBA', (background.size), (54,57,63,255))
    #blurple.paste(icon, offset)
    blurple.paste(background, (0, 0), background)
    draw = ImageDraw.Draw(blurple)

    draw.ellipse((offset[0] - 2, offset[1] - 2, 
                (offset[0])+icon_w + 2, (offset[1])+icon_h + 2), 
                fill='#36393f', outline="#ffffff", width=2)
    blurple.paste(icon, offset, icon)

    text_layer = Image.new("RGBA",(background.size), (0,0,0,0))
    draw = ImageDraw.Draw(text_layer)

    text_w, text_h = draw.textsize(member_msg, font=text_font)
    welc_w, welc_h = draw.textsize(server_msg, font=text_font)

    welc_layer = Image.new('RGBA', (welc_w,welc_h), (0,0,0,200))
    draw = ImageDraw.Draw(welc_layer)
    draw.text((0,0), server_msg, fill="white", font=text_font)

    username_layer = Image.new('RGBA', (text_w,text_h), (0,0,0,200))
    draw = ImageDraw.Draw(username_layer)
    draw.text((0,0), member_msg, fill="white", font=text_font)


    text_layer.paste(username_layer, ((bg_w-text_w)//2, bg_h-10-text_h), username_layer)
    text_layer.paste(welc_layer, ((bg_w-welc_w)//2, 10), welc_layer)

    final_img = Image.alpha_composite(blurple, text_layer)
    
    embed = discord.Embed(title="Ding dong!")
    
    embed.add_field(
        name= 'Member',
        value= member_msg,
        inline=False
    )
    
    embed.add_field(
        name= 'Account Creation Date',
        value= member.created_at,
        inline=False
    )
    
    file = None
    with io.BytesIO() as image_bin:
        final_img.save(image_bin, format='PNG')
        image_bin.seek(0)
        file = discord.File(image_bin, filename='welcome.png')
        embed.set_image(url='attachment://welcome.png')
        
    return embed, file