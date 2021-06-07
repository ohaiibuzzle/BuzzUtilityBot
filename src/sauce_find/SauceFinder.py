from discord.ext import commands
from .saucenao import find_sauce
from .embeds import construct_saucenao_embed_pixiv
from .iqdb import construct_iqdb_embed
import discord

class SauceFinder(commands.Cog, name='Picture Sauce Finding'):
  
    def __init__(self, client):
        self.client = client
        
    @commands.command(brief='Search for picture on SauceNAO, using Pixiv Database',
                      description='Search for a picture in an embed or attachment, using the SauceNAO engine.\n\
                          Pixiv only as of now. Twitter is scary')
    async def sauceplz(self, ctx):
        print ('@' + ctx.message.author.name + '#' + ctx.message.author.discriminator + ' try to find sauce!')
        async with ctx.channel.typing():
            if (ctx.message.reference):
                if (ctx.message.reference.resolved != None):
                    search_msg = ctx.message.reference.resolved
                    if (search_msg.embeds.__len__() > 0):
                        for attachment in search_msg.embeds:
                            if attachment.image != None:
                                try:
                                    found = await find_sauce(attachment.url)
                                    print(attachment.url)
                                    if found == None:
                                        await ctx.send("I am sssorry, can't get your sauce :(")
                                        await ctx.send("Ask Buzzle why that is")
                                    else:
                                        try:
                                            att_embed = await construct_saucenao_embed_pixiv(found)
                                            await ctx.send(embed=att_embed)
                                        except (discord.errors.HTTPException, AttributeError):
                                            await ctx.send('Something went wrong and I can\'t look up your image.')
                                            await ctx.send('Either it has been deleted or hidden by the author, or it isn\'t on Pixiv')
                                except TypeError:
                                    ctx.send("I couldn't find anything :(")
                    elif (search_msg.attachments.__len__() > 0):
                        for attachment in search_msg.attachments:
                            if attachment.content_type.startswith('image'):
                                found = await find_sauce(attachment.url)
                                print(attachment.url)
                                if found == None:
                                    await ctx.send("I am sssorry, can't get your sauce :(")
                                    await ctx.send("Ask Buzzle why that is")
                                else:
                                    try:
                                        att_embed = await construct_saucenao_embed_pixiv(found)
                                        await ctx.send(embed=att_embed)
                                    except (discord.errors.HTTPException, AttributeError):
                                        await ctx.send('Something went wrong and I can\'t look up your image.')
                                        await ctx.send('Either it has been deleted or hidden by the author, or it isn\'t on Pixiv')
            else:
                await ctx.send("Please mention a message containing pasta!")
                
    @commands.command(brief='Search for picture on IQDB',
                      description='Search for a picture in an embed or attachment, using the IQDB engine.\n\
                          Slower than SauceNAO, but has a higher search limit')
    async def iqdb(self, ctx):
        print ('@' + ctx.message.author.name + '#' + ctx.message.author.discriminator + ' try to find sauce on IQDB!')
        async with ctx.channel.typing():
            if (ctx.message.reference):
                if (ctx.message.reference.resolved != None):
                    search_msg = ctx.message.reference.resolved
                    if (search_msg.embeds.__len__() > 0):
                        for attachment in search_msg.embeds:
                            if attachment.image != None:
                                try:
                                    found = await construct_iqdb_embed(attachment.url)
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
                
def setup(client):
    client.add_cog(SauceFinder(client))