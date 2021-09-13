import discord
from discord.ext import commands
from utils.AdminTools import AdminTools
import os, sqlite3
import configparser

print("Starting up. This could take a while on slower devices while TensorFlow loads")

if not os.path.isdir('runtime'):
    os.mkdir('runtime')
    print("Please populate the /runtime directory with your credentials!")
    config = configparser.ConfigParser()
    config['Credentials']={
        'discord_key': '',
        'pixiv_key': '',
        'saucenao_key': '',
        'youtube_data_v3_key' : '',
        'spotify_web_api_cid' : '',
        'spotify_web_api_sec' : ''
    }
    with open('runtime/config.cfg', 'w+') as configfile:
        config.write(configfile)
    exit(0)

intents = discord.Intents.default()
intents.members = True # pylint: disable=assigning-non-slot

client = commands.Bot(command_prefix='.', intents=intents)

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
client.load_extension('utils.Welcome')
client.load_extension('utils.Birthday')
client.load_extension('utils.owo')
client.load_extension('music.Music')
#client.load_extension('utils.nsfwRole')

config = configparser.ConfigParser()
config.read('runtime/config.cfg')
client.run(config['Credentials']['discord_key'])