from discord.ext import commands, tasks
import discord
import asyncio
import aiosqlite, sqlite3
import datetime
import pytz

class Birthday(commands.Cog, name="Birthdays!"):
    RT_DATABASE = 'runtime/server_data.db'

    def cog_command_error(self, ctx, error):
        if error is AttributeError or error is commands.errors.MissingRequiredArgument:
            return ctx.send(f"There was an error processing your request (Perhaps checks your command?) \n Details:{error}")
        else:
            return ctx.send(f"There was an error processing your request \nDetails: {error}")

    def __init__(self,client):
        self.client = client
        db = sqlite3.connect(self.RT_DATABASE)
        curr = db.cursor()    
        curr.execute('''CREATE TABLE IF NOT EXISTS BirthdayMessage ([GuildID] INTEGER PRIMARY KEY, [ChannelID] Integer)''') 
        curr.execute('''CREATE TABLE IF NOT EXISTS Birthdays ([MemberID] INTEGER, [GuildID] INTEGER, [Birthday] TIMESTAMP, PRIMARY KEY ("MemberID","GuildID"))''') 
        db.close()
        open('runtime/today.status', 'a+')
        # pylint: disable=no-member
        self.sendBirthdayMessages.start() #This is actually fine
        
        
    def cog_unload(self):
        # pylint: disable=no-member
        self.sendBirthdayMessages.cancel() #This is actually fine
        
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        async with aiosqlite.connect(self.RT_DATABASE) as db:
            async with db.cursor() as curr:
                await curr.execute('''DELETE FROM Birthdays WHERE GuildID=:guildID AND MemberID=:memberID''',
                {'guildID': member.guild.id, 'memberID': member.id})
                await db.commit()

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        async with aiosqlite.connect(self.RT_DATABASE) as db:
            async with db.cursor() as curr:
                await curr.execute('''DELETE FROM Birthdays WHERE GuildID=:guildID''',
                {'guildID': guild.id})
                await curr.execute('''DELETE FROM BirthdayMessage WHERE GuildID=:guildID''',
                {'guildID': guild.id})
                await db.commit()

    @commands.command(brief="Setup birthday channel!")
    @commands.has_permissions(administrator=True)
    async def setupBirthday(self, ctx):
        async with aiosqlite.connect(self.RT_DATABASE) as db:
            async with db.cursor() as curr:
                if ctx.message.channel.type is discord.ChannelType.text:
                    await curr.execute('''DELETE FROM BirthdayMessage WHERE GuildID = :guildid''', {'guildid': ctx.guild.id})
                    await curr.execute('''INSERT INTO BirthdayMessage (GuildID, ChannelID)
                                VALUES (:guildid, :channelid)''',  {'guildid': ctx.guild.id, 'channelid': ctx.message.channel.id})
                    await db.commit()
                    await ctx.send("Success. This channel will now be used for birthday messages!")
                else:
                    await ctx.send("Cannot use this channel :<")
                pass
    
    @commands.command(brief="Unset birthday channel")
    @commands.has_permissions(administrator=True)
    async def clearBirthday(self, ctx):
        async with aiosqlite.connect(self.RT_DATABASE) as db:
            async with db.cursor() as curr:
                await curr.execute('''DELETE FROM BirthdayMessage WHERE GuildID = :guildid''', {'guildid': ctx.guild.id})
                await db.commit()
                await ctx.send("Success. Removed the birthday messages from this channel!")
    
    @commands.command(brief="Set your birthday", description='Set your birthday!. The bot will send a message when its time \n\
        Date follows [day] [month] [year]. Clear your birthday with "clear"')
    async def bday(self, ctx, *args):
        #print(args)
        async with aiosqlite.connect(self.RT_DATABASE) as db:
            async with db.cursor() as curr:        
                server = await db.execute('''SELECT GuildID, ChannelID FROM BirthdayMessage WHERE GuildID=:guildid''', {'guildid': ctx.guild.id})
                server_info = await server.fetchone()
                if server_info == None:
                    await ctx.send("This server has not been set up for birthday messages, yet!")
                    return
                
                if args[0] == 'clear':
                    await curr.execute('''DELETE FROM Birthdays WHERE GuildID=:guildID AND MemberID=:memberID''', 
                                    {'guildID': ctx.guild.id, 'memberID': ctx.author.id})
                    await db.commit()
                    await ctx.send("Cleared your birthday from the database!")
                    return

                if args[0].isnumeric() and args[1].isnumeric() and args[2].isnumeric():
                    try:
                        await curr.execute('''DELETE FROM Birthdays WHERE MemberID=:memberID and GuildID=:guildID''',
                                           {'memberID': ctx.author.id, 'guildID': ctx.guild.id})
                        bday = datetime.datetime(day=int(args[0]), month=int(args[1]), year=int(args[2]))
                        await curr.execute('''INSERT INTO Birthdays (MemberID, GuildID, Birthday) 
                                                VALUES (:memberID, :guildID, :birthday)''', 
                                                {'memberID': ctx.author.id, 'guildID': ctx.guild.id, 'birthday': bday})
                        await db.commit()
                        await ctx.send("Your birthday has been set to {}/{}/{}".format(args[0], args[1], args[2]))
                        return
                    except ValueError:
                        await ctx.send("Hey, are you sure those are numbers???")
                        return
                await ctx.send("Uhhh what the hell even happened. How do you even get here?")
                pass
    
    @tasks.loop(seconds=30.0)
    async def sendBirthdayMessages(self):
        tz = pytz.timezone('Asia/Tokyo')
        today_mmdd = '%{}%'.format(datetime.datetime.now(tz).strftime("%m-%d"))
        #print(today_mmdd)
        with open('runtime/today.status', 'r') as today_file:
            today_mmdd_file = today_file.readline()
            #print(today_mmdd_file)
            if today_mmdd_file == today_mmdd:   
                return
            
        async with aiosqlite.connect(self.RT_DATABASE) as db:
            async with db.execute('''SELECT MemberID, GuildID FROM Birthdays WHERE Birthday LIKE :currentDate''',
                                    {'currentDate': today_mmdd}) as cursor:
                async for row in cursor:
                    #print(row)
                    server_info = await(await db.execute('''SELECT ChannelID FROM BirthdayMessage WHERE GuildID = :guildID''', {'guildID': row[1]})).fetchone()
                    if server_info != None:
                        channel = discord.utils.get(self.client.get_all_channels(), id = server_info[0])
                        await channel.send("Hey, happy birthday to <@{}>!".format(row[0]))
        
        with open('runtime/today.status', 'w+') as today_file:
            today_file.write(today_mmdd)
            print("Done for today!")

def setup(client):
    client.add_cog(Birthday(client))
    