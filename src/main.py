import discord
from discord.ext import commands

client = discord.Client()

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

key = ''
with open(api.key, 'r') as keyfile:
    key = keyfile.readline()

client.run(key)