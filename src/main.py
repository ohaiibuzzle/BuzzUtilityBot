import discord
from discord.ext import commands
from pic_source.PictureSearch import PictureSearch
from sauce_find.SauceFinder import SauceFinder
from utils.MessageUtils import MessageUtils
from tf_image_processor.TFImage import TFImage

client = commands.Bot(command_prefix='.', owner_id=169257697345011712)

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    game = discord.Game("in Buzzle's Box. Available on GitHub")
    await client.change_presence(status=discord.Status.online, activity=game)

client.add_cog(PictureSearch(client))
client.add_cog(SauceFinder(client))
client.add_cog(MessageUtils(client))
client.add_cog(TFImage(client))

key = ''
with open('discord.key', 'r') as keyfile:
    key = keyfile.readline()
client.run(key)