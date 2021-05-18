import discord

image_format = ['.jpg', '.JPG',
                '.png', '.PNG',
                '.gif']

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
    