import discord
from discord.ext import commands, bridge

from utils.AdminTools import AdminTools
from config_reader import GLOBAL_CONFIG as config

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Now we change the logging level
logging.getLogger().setLevel(logging.getLevelName(config["Features"]["log_level"]))
if config["Features"]["log_file"]:
    logging.getLogger().addHandler(logging.FileHandler(config["Features"]["log_file"]))
logging.info("Starting up...")

intents = discord.Intents.default()
intents.members = True  # pylint: disable=assigning-non-slot
intents.message_content = True

client = bridge.Bot(command_prefix=config["Features"]["prefix"], intents=intents)


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
