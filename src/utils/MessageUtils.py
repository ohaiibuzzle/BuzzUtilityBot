from discord.ext import commands
import discord
from utils.embeds import construct_save_embed_img

class MessageUtils(commands.Cog, name='Message Utilities'):
    def __init__(self, client):
        self.client = client
        
    @commands.command(brief='Save a message to your DM', 
                      description='Save whatever message you mention when this command is ran. \
                      If no message is mentioned, save the last message that has an embed in it')
    async def savethis(self, ctx):
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
                
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.client.user:
            return
        
        if message.content.startswith('. so I can save'):
            messages = await message.channel.history(limit=10).flatten()
            for mesg in messages:
                if mesg.attachments.__len__() > 0 or mesg.embeds.__len__() > 0:
                    await message.author.send(embed=construct_save_embed_img(mesg))
                    break
    
    @commands.command(brief='Delete the last message the bot send',
                      description='Use this command to delete the bot\'s last message. \
                          Used in case things went wrong')
    
    async def oofie(self,ctx):
        print ('Uh oh, @' + ctx.message.author.name + '#' + ctx.message.author.discriminator + ' told us we messed up!')
        await ctx.message.delete()
        messages = await ctx.channel.history(limit=10).flatten()
        for mesg in messages:
            if mesg.author == self.client.user:
                await mesg.delete()
                break
