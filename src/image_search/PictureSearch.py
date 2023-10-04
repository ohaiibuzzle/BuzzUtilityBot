import asyncio
import re
import configparser
import logging

import aioredis
import discord
from discord.ext import commands, bridge

from .danbooru import search_danbooru
from .pixiv import construct_pixiv_embed, get_image_by_id
from .safebooru import safebooru_random_img
from .zerochan import search_zerochan

# load config for redis
config = configparser.ConfigParser()
config.read("runtime/config.cfg")
redis_host = config["Dependancies"]["redis_host"]


class PictureSearch(commands.Cog, name="Random image finder"):
    def __init__(self, client):
        self.client = client
        self.redis_pool = aioredis.from_url(redis_host, decode_responses=True)

    def cog_command_error(self, ctx, error):
        if error is AttributeError or error is commands.errors.MissingRequiredArgument:
            return ctx.respond(
                f"There was an error processing your request (Perhaps checks your command?) \n Details:{error}"
            )
        else:
            return ctx.respond(
                f"There was an error processing your request \nDetails: {error}"
            )

    @bridge.bridge_command(
        brief="Random image from SafeBooru",
        aliases=["sbr"],
    )
    async def sbrandom(self, ctx, *, tags):
        """
        Look for a random image on SafeBooru, input can be any of SafeBooru's tag query

        Combine tags using "+"
        """
        logging.info(
            "@"
            + ctx.author.name
            + "#"
            + ctx.author.discriminator
            + " wants something random (SafeBooru)!"
        )
        await ctx.defer()
        try:
            target = await safebooru_random_img(tags.split("+"), ctx.channel)
        except ConnectionError:
            await ctx.respond(
                "Buzzle's Internet broke :(\n(Try again in a few minutes, server is under high load)"
            )
        else:
            if target:
                await ctx.respond(embed=target)
                try:
                    await self.redis_pool.set(
                        f"{ctx.channel.id}:{ctx.author.id}",
                        f"SAFEBOORU {tags}",
                        ex=15,
                    )
                except:
                    msg = await ctx.respond(
                        "Buzzle forgot to start Redis, so I won't remember your command :("
                    )
                    await asyncio.sleep(5)
                    await msg.delete()
            else:
                await ctx.respond("Your search returned no result :(")

    @bridge.bridge_command(
        brief="Random image from ZeroChan",
        aliases=["zcr"],
    )
    async def zcrandom(self, ctx, *, tags):
        """
        Look for a random image on ZeroChan, input can be any of ZeroChan's tag query

        Combine tags using "+"
        """
        await ctx.defer()
        logging.info(
            "@"
            + ctx.author.name
            + "#"
            + ctx.author.discriminator
            + " wants something random (zerochan)!"
        )
        tags = tags.replace("+", ",")
        try:
            res = await self.construct_zerochan_embed(ctx.channel, tags)
        except TypeError as e:
            logging.warning(e)
            await ctx.respond(
                "Your search string was wonky, or it included NSFW tags.\nTry again"
            )
            return
        except ConnectionError:
            await ctx.respond(
                "Buzzle's Internet broke :(\n(Try again in a few minutes, server is under high load)"
            )
        else:
            if res != None:
                await ctx.respond(embed=res)
                try:
                    await self.redis_pool.set(
                        f"{ctx.channel.id}:{ctx.author.id}",
                        f"ZEROCHAN {tags}",
                        ex=15,
                    )
                except:
                    msg = await ctx.respond(
                        "Buzzle forgot to start Redis, so I won't remember your command :("
                    )
                    await asyncio.sleep(5)
                    await msg.delete()
            else:
                await ctx.respond(
                    "Sorry, I can't find you anything :( \nEither check your search, or Buzzle banned a tag in the result"
                )

    @bridge.bridge_command(
        brief="Look for a random image on Pixiv",
        aliases=["pxr"],
    )
    async def pixivrandom(self, ctx, *, tags):
        """
        Look for a random image on Pixiv
        """
        await ctx.defer()
        logging.info(
            "@"
            + ctx.author.name
            + "#"
            + ctx.author.discriminator
            + " wants something random (Pixiv)!"
        )
        try:
            target, file = await construct_pixiv_embed(tags, ctx.channel)
        except ConnectionError:
            await ctx.respond(
                "Buzzle's Internet broke :(\n(Try again in a few minutes, server is under high load)"
            )
        except ValueError:
            await ctx.respond("Nothing found :(\nCheck your query")
        else:
            if target:
                await ctx.respond(embed=target, file=file)
                try:
                    await self.redis_pool.set(
                        f"{ctx.channel.id}:{ctx.author.id}", f"PIXIV {tags}", ex=15
                    )
                except:
                    msg = await ctx.respond(
                        "Buzzle forgot to start Redis, so I won't remember your command :("
                    )
                    await asyncio.sleep(5)
                    await msg.delete()
            else:
                await ctx.respond("Your search returned no result :(")

    @bridge.bridge_command(
        brief="Display a Pixiv post in bot's format", aliases=["pxs"]
    )
    async def pixivshow(self, ctx, *, url_or_illustid):
        """
        Formats Pixiv arts in a way that makes it less... bad
        """
        await ctx.defer()
        logging.info(
            "@"
            + ctx.author.name
            + "#"
            + ctx.author.discriminator
            + " wants to display Pixiv art!"
        )
        # if the url is just the illust id
        if url_or_illustid.isdigit():
            illust_id = url_or_illustid
        else:
            illust_id = re.findall(r"\d+", url_or_illustid)[0]
        try:
            target, file = await get_image_by_id(illust_id)
        except ConnectionError:
            await ctx.respond(
                "Buzzle's Internet broke :(\n(Try again in a few minutes, server is under high load)",
            )
        except ValueError:
            await ctx.respond("Nothing found :(\nCheck your query")
        except TypeError:
            # Most likely because it returns None, which signifies that the image is restricted
            await ctx.respond("This image is restricted :(")
        else:
            if target:
                await ctx.respond(
                    f"Image fetched for {ctx.author.name}", embed=target, file=file
                )
            else:
                await ctx.respond("Your search returned no result :(")
        if isinstance(ctx, bridge.BridgeExtContext):
            await ctx.message.delete()  # this is a url, so we wipe it to get rid of duped

    pass

    @bridge.bridge_command(
        brief="Danbooru (NSFW) search",
        aliases=["dbr"],
    )
    async def danboorurandom(self, ctx: commands.Context, *, tags):
        """
        Search for a random image on Danbooru."
        """
        await ctx.defer()
        logging.info(
            "@"
            + ctx.author.name
            + "#"
            + ctx.author.discriminator
            + " wants to search danbooru!"
        )
        try:
            if not ctx.channel.is_nsfw():
                await ctx.respond(
                    "This command cannot be ran on channels that aren't marked NSFW!"
                )
                return
        except AttributeError:
            await ctx.respond(
                "This command cannot be ran on channels that aren't marked NSFW!"
            )
            return
        try:
            embed = await PictureSearch.construct_danbooru_embed(tags)
        except ConnectionError:
            await ctx.respond(
                "Buzzle's Internet broke :(\n(Try again in a few minutes, server is under high load)"
            )
        else:
            await ctx.respond(embed=embed)
            try:
                await self.redis_pool.set(
                    f"{ctx.channel.id}:{ctx.author.id}", f"DANBOORU {tags}", ex=15
                )
            except:
                msg = await ctx.respond(
                    "Buzzle forgot to start Redis, so I won't remember your command :("
                )
                await asyncio.sleep(5)
                await msg.delete()

    @bridge.bridge_command(
        brief="Execute the last command, again!",
    )
    async def more(self, ctx: commands.Context):
        """
        Run the last command you executed, timeout is 15s

        Only some commands are supported.
        """
        last_exec = await self.redis_pool.get(f"{ctx.channel.id}:{ctx.author.id}")
        if last_exec is None:
            await ctx.respond("I can't remember what you were doing~~")
            return
        last_exec = str(last_exec)
        if last_exec.startswith("ZEROCHAN"):
            # await self.zcrandom(ctx, tags=last_exec[9:])
            ctx.message.content = f"{ctx.prefix}zcr {last_exec[9:]}"
            await self.client.process_commands(ctx.message)
        elif last_exec.startswith("SAFEBOORU"):
            # await self.sbrandom(ctx, tags=last_exec[10:])
            ctx.message.content = f"{ctx.prefix}sbr {last_exec[10:]}"
            await self.client.process_commands(ctx.message)
        elif last_exec.startswith("PIXIV"):
            # await self.pixivrandom(ctx, tags=last_exec[6:])
            ctx.message.content = f"{ctx.prefix}pxr {last_exec[6:]}"
            await self.client.process_commands(ctx.message)
        elif last_exec.startswith("DANBOORU"):
            # await self.danboorurandom(ctx, tags=last_exec[9:])
            ctx.message.content = f"{ctx.prefix}dbr {last_exec[9:]}"
            await self.client.process_commands(ctx.message)

    @staticmethod
    async def construct_zerochan_embed(ch, query: str) -> discord.Embed:
        """Make a Zerochan embed

        Args:
            ch (discord.Channel): A Discord channel (to check whether it is NSFW)
            query (str): The query

        Returns:
            discord.Embed: The embed with the picture
        """
        if ch.type is not discord.ChannelType.private:
            res = await search_zerochan(ch.is_nsfw(), query)
        else:
            res = await search_zerochan(True, query)
        if res == None:
            return None
        else:
            embed = discord.Embed(title=res["title"])
            embed.url = res["link"]
            embed.set_image(url=res["content"])

            embed.add_field(name="Source", value=embed.url, inline=False)
            embed.add_field(
                name="Tags",
                value="```\n" + res["keywords"][:1018] + "\n```",
                inline=False,
            )
            return embed

    @staticmethod
    async def construct_danbooru_embed(query: str) -> discord.Embed:
        """Make a Danbooru embed with a random image from query

        Args:
            query (str): The query to look for

        Returns:
            discord.Embed: The embed
        """
        res = await search_danbooru(query)
        embed = discord.Embed(title=query)
        embed.url = f"https://danbooru.donmai.us/posts/{res['id']}"
        if res["has_large"]:
            embed.set_image(url=res["large_file_url"])
        else:
            embed.set_image(url=res["file_url"])

        embed.add_field(name="Source", value=res["source"], inline=False)
        embed.add_field(
            name="Tags",
            value="```\n" + res["tag_string"][:1018] + "\n```",
            inline=False,
        )
        return embed


def setup(client):
    client.add_cog(PictureSearch(client))
