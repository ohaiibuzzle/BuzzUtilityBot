import discord
from discord.ext import commands, bridge

from utils.AdminTools import AdminTools
import os
import configparser
import asyncio

print("Starting up...")

if not os.path.isdir("runtime"):
    os.mkdir("runtime")
    os.mkdir("runtime/models")
    print("Please populate the /runtime directory with your credentials!")
    config = configparser.ConfigParser()
    config["Credentials"] = {
        "discord_key": "",
        "pixiv_key": "",
        "saucenao_key": "",
        "youtube_data_v3_key": "",
        "spotify_web_api_cid": "",
        "spotify_web_api_sec": "",
        "twitter_bearer_token": "",
    }

    config["Dependancies"] = {
        "nsfw_model_path": "runtime/models/mobileNet.tflite",
        "nsfw_image_dim": "224",
        "redis_host": "redis://localhost",
    }

    with open("runtime/config.cfg", "w+") as configfile:
        config.write(configfile)
    exit(0)

try:
    import uvloop
except ModuleNotFoundError:
    pass
else:
    print("Installing UVLoop...")
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


intents = discord.Intents.default()
intents.members = True  # pylint: disable=assigning-non-slot
intents.message_content = True

client = bridge.Bot(command_prefix=".", intents=intents)


@client.event
async def on_ready():
    print("We have logged in as {0.user}".format(client))
    game = discord.Game("in Buzzle's Box. Available on GitHub")
    await client.change_presence(status=discord.Status.online, activity=game)


client.add_cog(AdminTools(client))

client.load_extension("pic_source.PictureSearch")
client.load_extension("sauce_find.SauceFinder")
client.load_extension("tf_image_processor.TFImage")
client.load_extension("utils.MessageUtils")
client.load_extension("utils.Welcome")
client.load_extension("utils.Birthday")
client.load_extension("utils.owo")
client.load_extension("music.Music")
client.load_extension("twitterwatch.TwitterWatcher")
# client.load_extension("utils.nsfwRole")

config = configparser.ConfigParser()
config.read("runtime/config.cfg")
client.run(config["Credentials"]["discord_key"])
