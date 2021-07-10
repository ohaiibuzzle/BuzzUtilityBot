from discord.ext import commands
import discord
import sqlite3
import aiosqlite

from .embeds import construct_welcome_embed

class WelcomeMessage(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.db = sqlite3.connect('runtime/server_data.db')
        self.curr = self.db.cursor()    
        self.curr.execute('''CREATE TABLE IF NOT EXISTS WelcomeMessage ([GuildID] INTEGER PRIMARY KEY, [ChannelID] Integer)''')   
        
    @commands.Cog.listener()
    async def on_member_join(self,member):
        async with aiosqlite.connect('runtime/server_data.db') as db:
            async with db.cursor() as curr:
                server = await curr.execute('''SELECT GuildID, ChannelID FROM WelcomeMessage WHERE GuildID=:guildid''', {'guildid': member.guild.id})
                server_info = await server.fetchone()
                if server_info != None:
                    channel = discord.utils.get(member.guild.channels, id=server_info[1])
                    embed, file = await construct_welcome_embed(member)
                    await channel.send(file=file, embed=embed)
                pass
    
    @commands.command(brief="Use this channel for welcome messages")
    @commands.has_permissions(administrator=True)
    async def setupWelcome(self,ctx):
        if ctx.message.channel.type is discord.ChannelType.text:
            self.curr.execute('''DELETE FROM WelcomeMessage WHERE GuildID = :guildid''', {'guildid': ctx.guild.id})
            self.curr.execute('''INSERT INTO WelcomeMessage (GuildID, ChannelID)
                        VALUES (:guildid, :channelid)''',  {'guildid': ctx.guild.id, 'channelid': ctx.message.channel.id})
            self.db.commit()
            await ctx.send("Success. This channel will now be used for welcome messages!")
        else:
            await ctx.send("Cannot use this channel :<")
    
    @commands.command(brief="Unset this channel for welcome messages")
    @commands.has_permissions(administrator=True)
    async def clearWelcome(self, ctx):
        self.curr.execute('''DELETE FROM WelcomeMessage WHERE GuildID = :guildid''', {'guildid': ctx.guild.id})
        self.db.commit()
        await ctx.send("Success. Removed the welcome messages from this channel!")

def setup(client):
    client.add_cog(WelcomeMessage(client))
    