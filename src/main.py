import discord
from discord.ext import commands
from saucenao import find_sauce

game = discord.Game("In Buzzle's Development Environment!")

client = commands.Bot(command_prefix='.', help_command=None, owner_id=169257697345011712, activity=game)

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
                await message.author.send('Saved it for ya!')
                await message.author.send(mesg.jump_url)
                break

    await client.process_commands(message)

@client.command()
async def sauceplz(ctx):
    if (ctx.message.reference):
        if (ctx.message.reference.resolved != None):
            search_msg = ctx.message.reference.resolved
            if (search_msg.embeds.__len__() > 0):
                for attachment in search_msg.embeds:
                    if attachment.image != None:
                        found = find_sauce(attachment.url)
                        print(attachment.url)
                        if found == None:
                            await ctx.send("I am sssorry, can't get your sauce :(")
                            await ctx.send("Ask Buzzle why that is")
                        else:
                            await ctx.send(found)
    else:
        await ctx.send("Please mention a message containing pasta!")

key = ''
with open('discord.key', 'r') as keyfile:
    key = keyfile.readline()
client.run(key)