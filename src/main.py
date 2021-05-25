import discord
from discord.ext import commands
from utils.AdminTools import AdminTools

client = commands.Bot(command_prefix='.')

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    game = discord.Game("in Buzzle's Box. Available on GitHub")
    await client.change_presence(status=discord.Status.online, activity=game)

client.add_cog(AdminTools(client))

client.load_extension('pic_source.PictureSearch')
client.load_extension('sauce_find.SauceFinder')
client.load_extension('tf_image_processor.TFImage')
client.load_extension('utils.MessageUtils')

key = ''
with open('discord.key', 'r') as keyfile:
    key = keyfile.readline()
client.run(key)