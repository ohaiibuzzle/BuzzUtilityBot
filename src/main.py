import discord
from discord.ext import commands
from saucenao import find_sauce
from embeds import construct_saucenao_embed_pixiv, construct_save_embed_img
from zerochan import construct_zerochan_embed
from safebooru import random_image
from iqdb import construct_iqdb_embed

game = discord.Game("In Buzzle's Development Environment!")

client = commands.Bot(command_prefix='.', owner_id=169257697345011712, activity=game)

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    game = discord.Game("in Buzzle's Box. Available on GitHub")
    await client.change_presence(status=discord.Status.online, activity=game)

@client.event   
async def on_message(message):
    if message.author == client.user:
        return
    
    if message.content.startswith('. so I can save'):
        messages = await message.channel.history(limit=10).flatten()
        for mesg in messages:
            if mesg.attachments.__len__() > 0 or mesg.embeds.__len__() > 0:
                await message.author.send(embed=construct_save_embed_img(mesg))
                break
    await client.process_commands(message)

@client.command()
async def sauceplz(ctx):
    print ('@' + ctx.message.author.name + '#' + ctx.message.author.discriminator + ' try to find sauce!')
    async with ctx.channel.typing():
        if (ctx.message.reference):
            if (ctx.message.reference.resolved != None):
                search_msg = ctx.message.reference.resolved
                if (search_msg.embeds.__len__() > 0):
                    for attachment in search_msg.embeds:
                        if attachment.image != None:
                            try:
                                found = find_sauce(attachment.url)
                                print(attachment.url)
                                if found == None:
                                    await ctx.send("I am sssorry, can't get your sauce :(")
                                    await ctx.send("Ask Buzzle why that is")
                                else:
                                    try:
                                        att_embed = construct_saucenao_embed_pixiv(found)
                                        await ctx.send(embed=att_embed)
                                    except (discord.errors.HTTPException, AttributeError):
                                        await ctx.send('Something went wrong and I can\'t look up your image.')
                                        await ctx.send('Either it has been deleted or hidden by the author, or it isn\'t on Pixiv')
                            except TypeError:
                                ctx.send("I couldn't find anything :(")
                elif (search_msg.attachments.__len__() > 0):
                    for attachment in search_msg.attachments:
                        if attachment.content_type.startswith('image'):
                            found = find_sauce(attachment.url)
                            print(attachment.url)
                            if found == None:
                                await ctx.send("I am sssorry, can't get your sauce :(")
                                await ctx.send("Ask Buzzle why that is")
                            else:
                                try:
                                    att_embed = construct_saucenao_embed_pixiv(found)
                                    await ctx.send(embed=att_embed)
                                except (discord.errors.HTTPException, AttributeError):
                                    await ctx.send('Something went wrong and I can\'t look up your image.')
                                    await ctx.send('Either it has been deleted or hidden by the author, or it isn\'t on Pixiv')
        else:
            await ctx.send("Please mention a message containing pasta!")

@client.command()
async def savethis(ctx):
    print ('@' + ctx.message.author.name + '#' + ctx.message.author.discriminator + ' try to save!')
    if (ctx.message.reference):
        if (ctx.message.reference.resolved != None):
            search_msg = ctx.message.reference.resolved
            await ctx.message.author.send(embed=construct_save_embed_img(search_msg))

    else:
        messages = await ctx.message.channel.history(limit=10).flatten()
        for mesg in messages:
            if mesg.attachments.__len__() > 0 or mesg.embeds.__len__() > 0:
                await ctx.message.author.send(embed=construct_save_embed_img(mesg))
                break

@client.command()
async def sbrandom(ctx, *args):
    print ('@' + ctx.message.author.name + '#' + ctx.message.author.discriminator + ' wants something random (SafeBooru)!')
    async with ctx.channel.typing():
        tags = ' '.join(args)
        tags = tags.replace('+', ',')
        target = random_image(tags.split('+'))
        if target:
            await ctx.send(embed=target)
        else:
            await ctx.send("Your search returned no result :(")           

@client.command()
async def oofie(ctx):
    print ('Uh oh, @' + ctx.message.author.name + '#' + ctx.message.author.discriminator + ' told us we messed up!')
    await ctx.message.delete()
    messages = await ctx.channel.history(limit=10).flatten()
    for mesg in messages:
        if mesg.author == client.user:
            await mesg.delete()
            break

@client.command()
async def iqdb(ctx):
    print ('@' + ctx.message.author.name + '#' + ctx.message.author.discriminator + ' try to find sauce on IQDB!')
    async with ctx.channel.typing():
        if (ctx.message.reference):
            if (ctx.message.reference.resolved != None):
                search_msg = ctx.message.reference.resolved
                if (search_msg.embeds.__len__() > 0):
                    for attachment in search_msg.embeds:
                        if attachment.image != None:
                            try:
                                found = construct_iqdb_embed(attachment.url)
                                print(attachment.url)
                                if found == None:
                                    await ctx.send("I am sssorry, can't get your sauce :(")
                                    await ctx.send("Ask Buzzle why that is")
                                else:
                                    try:
                                        await ctx.send(embed=found)
                                    except (discord.errors.HTTPException, AttributeError):
                                        await ctx.send('Something went wrong and I can\'t look up your image.')
                                        await ctx.send('Either it has been deleted or hidden by the author, or it isn\'t on Pixiv')
                            except TypeError:
                                await ctx.send("I couldn't find anything :(")
                elif (search_msg.attachments.__len__() > 0):
                    for attachment in search_msg.attachments:
                        if attachment.content_type.startswith('image'):
                            found = construct_iqdb_embed(attachment.url)
                            if found == None:
                                await ctx.send("I am sssorry, can't get your sauce :(")
                                await ctx.send("Ask Buzzle why that is")
                            else:
                                try:
                                    await ctx.send(embed=found)
                                except (discord.errors.HTTPException, AttributeError):
                                    await ctx.send('Something went wrong and I can\'t look up your image.')
                                    await ctx.send('Either it has batt_embedeen deleted or hidden by the author, or it isn\'t on Pixiv')
        else:
            await ctx.send("Please mention a message containing pasta!")

@client.command()
async def zcrandom(ctx, *args):
    with ctx.channel.typing():
        print ('@' + ctx.message.author.name + '#' + ctx.message.author.discriminator + ' wants something random(zerochan)!')
        tags = ' '.join(args).strip()
        tags = tags.replace('+', ',')
        try:
            res = construct_zerochan_embed(ctx.channel, tags)
        except TypeError:
            await ctx.send('Your search string was too wide, or it included NSFW tags.\nNarrow the query to try again')
            return
        if res != None:
            await ctx.send(embed=res)
        else:
            await ctx.send("Sorry, I can't find you anything :( \nEither check your search, or Buzzle banned a tag in the result")

key = ''
with open('discord.key', 'r') as keyfile:
    key = keyfile.readline()
client.run(key)