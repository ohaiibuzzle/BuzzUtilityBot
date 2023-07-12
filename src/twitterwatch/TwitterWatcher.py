import configparser
import random
import sqlite3

import aiohttp
import aiosqlite
from discord.ext import commands
import pnytter

from . import tweetstream

config = configparser.RawConfigParser()
config.read("runtime/config.cfg")


class TwitterWatcher(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.instances = config["Dependancies"]["nitter_instances"].split(",")

        # Initializing the tweetstream
        self.tweetstream = tweetstream.TweetStreamer(
            pnytter_instances=self.instances,
            callback=self.on_tweet, wait_time=config["Dependancies"]["tweetwatch_wait_time"],
        )

        # Initializing database
        database = sqlite3.connect("runtime/server_data.db")
        cursor = database.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tweetwatch (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                twitter_account TEXT UNIQUE,
                watching_channels TEXT
            )
            """
        )

        # Load the watching list from the database
        cursor.execute("SELECT twitter_account FROM tweetwatch")
        self.tweetstream.users = [row[0] for row in cursor.fetchall()]
        database.commit()
        pass

    @commands.Cog.listener()
    async def on_ready(self):
        self.tweetstream.start(self.tweetstream.users)

    async def restart_stream(self):
        self.tweetstream.stop()
        self.tweetstream.start(self.tweetstream.users)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def tweetwatch(self, ctx, *, twitter_account):
        """
        Add a twitter account to the watching list
        """
        channel = ctx.channel.id
        # Check if the account is already being watched
        async with aiosqlite.connect("runtime/server_data.db") as db:
            cursor = await db.execute(
                "SELECT * FROM tweetwatch WHERE twitter_account = ?",
                (twitter_account,),
            )
            row = await cursor.fetchone()
            if row:
                # pull out the channel list
                channels = row[2].split(",")
                if str(channel) in channels:
                    await ctx.send(
                        f"{twitter_account} is already being watched in this channel."
                    )
                    return await db.commit()

                else:
                    # add the channel to the list
                    channels.append(str(channel))
                    await db.execute(
                        "UPDATE tweetwatch SET watching_channels = ? WHERE twitter_account = ?",
                        (",".join(channels), twitter_account),
                    )
                    self.tweetstream.users.append(twitter_account)
                    await self.restart_stream()
                    await ctx.send(
                        f"{twitter_account} is now being watched in this channel."
                    )

                    return await db.commit()
            else:
                # add the account to the database
                await db.execute(
                    "INSERT INTO tweetwatch (twitter_account, watching_channels) VALUES (?, ?)",
                    (twitter_account, str(channel)),
                )

                self.tweetstream.users.append(twitter_account)
                await self.restart_stream()
                await ctx.send(
                    f"{twitter_account} is now being watched in this channel."
                )
                return await db.commit()

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def tweetunwatch(self, ctx, *, twitter_account):
        """
        Stop watching a twitter account
        """
        channel = ctx.channel.id
        # Check if the account is already being watched
        async with aiosqlite.connect("runtime/server_data.db") as db:
            cursor = await db.execute(
                "SELECT * FROM tweetwatch WHERE twitter_account = ?",
                (twitter_account,),
            )
            row = await cursor.fetchone()
            if row:
                # pull out the channel list
                channels = row[2].split(",")
                if str(channel) in channels:
                    # remove the channel from the list
                    channels.remove(str(channel))
                    # if the list is empty, delete the row
                    if not channels:
                        await db.execute(
                            "DELETE FROM tweetwatch WHERE twitter_account = ?",
                            (twitter_account,),
                        )
                        self.tweetstream.users.remove(twitter_account)
                        await self.restart_stream()
                    else:
                        await db.execute(
                            "UPDATE tweetwatch SET watching_channels = ? WHERE twitter_account = ?",
                            (",".join(channels), twitter_account),
                        )
                    await db.commit()
                    await ctx.send(
                        f"{twitter_account} is no longer being watched in this channel."
                    )
                    return
                else:
                    await ctx.send(
                        f"{twitter_account} is not being watched in this channel."
                    )
                    return
            else:
                await ctx.send(f"{twitter_account} is not being watched.")
                return

    async def on_tweet(self, tweet: pnytter.models.TwitterTweet, profile: pnytter.models.profiles.TwitterProfile):
        """
        Callback for the tweetstream
        """
        print(f"Received tweet from {profile.username}: {tweet.tweet_id}")
        # Get the channel list from the database
        async with aiosqlite.connect("runtime/server_data.db") as db:
            cursor = await db.execute(
                "SELECT * FROM tweetwatch WHERE twitter_account = ?",
                (profile.username,),
            )
            row = await cursor.fetchone()
            if row:
                channels = row[2].split(",")
                for channel in channels:
                    channel = self.client.get_channel(int(channel))
                    if channel:
                        # Create a webhook, using the unavatar.io service for the avatar
                        async with aiohttp.ClientSession() as session:
                            nitter_path = profile.pictures.profile.nitter_path
                            if nitter_path:
                                url = random.choice(self.instances) + nitter_path
                                print(url)
                                async with session.get(
                                    url
                                ) as response:
                                    avatar = await response.read()
                            else:
                                avatar = None
                        webhook = await channel.create_webhook(
                            name=f"{profile.username} - {profile.fullname}", avatar=avatar
                        )
                        # Send the tweet
                        await webhook.send(
                            f"https://fxtwitter.com/{tweet.author}/status/{tweet.tweet_id}"
                        )
                        # Delete the webhook
                        await webhook.delete()
            await db.commit()

    def __del__(self):
        self.tweetstream.stop()


def setup(client):
    print("Loading Twitter Watcher...")
    client.add_cog(TwitterWatcher(client))
