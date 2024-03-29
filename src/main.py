import discord
from discord.ext import commands, bridge

from utils.AdminTools import AdminTools
import os
import configparser
import asyncio

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

HAS_CONFIG = True

if not os.path.exists("runtime"):
    os.mkdir("runtime")
    os.mkdir("runtime/models")
    HAS_CONFIG = False

if not os.path.exists("runtime/config.cfg"):
    logging.critical("No config file found!")
    HAS_CONFIG = False

if not HAS_CONFIG:
    logging.critical("Please populate the /runtime directory with your credentials!")
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
        "nsfw_tflite_threads": "1",
        "redis_host": "redis://redis",
        "nitter_instances": "",
        "tweetwatch_wait_time": "60",
    }

    config["Features"] = {
        "blacklisted_features": "utils.nsfwRole",
        "log_level": "WARNING",
        "log_file": "",
    }

    with open("runtime/config.cfg", "w+") as configfile:
        config.write(configfile)
    exit(0)

config = configparser.ConfigParser()
config.read("runtime/config.cfg")

# Now we change the logging level
logging.getLogger().setLevel(logging.getLevelName(config["Features"]["log_level"]))
if config["Features"]["log_file"]:
    logging.getLogger().addHandler(logging.FileHandler(config["Features"]["log_file"]))
logging.info("Starting up...")

try:
    import uvloop
except ModuleNotFoundError:
    pass
else:
    logging.info("Installing UVLoop...")
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


intents = discord.Intents.default()
intents.members = True  # pylint: disable=assigning-non-slot
intents.message_content = True

client = bridge.Bot(command_prefix=".", intents=intents)


@client.event
async def on_ready():
    logging.info("Logged in as {0.user}".format(client))
    game = discord.Game("in Buzzle's Box. Available on GitHub")
    await client.change_presence(status=discord.Status.online, activity=game)


client.add_cog(AdminTools(client))

features = [
    "image_search.PictureSearch",
    "image_lookup.SauceFinder",
    "image_analyze.TFImage",
    "utils.MessageUtils",
    "utils.Welcome",
    "utils.Birthday",
    "utils.owo",
    "music.Music",
    "utils.nsfwRole",
    "twitterwatch.TwitterWatcher",
]

blacklisted_features = config["Features"]["blacklisted_features"].split(",")

for feature in features:
    if feature not in blacklisted_features:
        client.load_extension(feature)
    else:
        logging.info(f"Skipping {feature} as it is blacklisted.")

client.run(config["Credentials"]["discord_key"])
