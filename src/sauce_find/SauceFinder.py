from discord.ext import commands
from .saucenao import find_sauce
from .iqdb import get_sauce
import discord
import configparser
from pysaucenao.saucenao import SauceNaoResults

config = configparser.ConfigParser()
config.read("runtime/config.cfg")


class SauceFinder(commands.Cog, name="Picture Sauce Finding"):
    def __init__(self, client):
        self.client = client

    #    def cog_command_error(self, ctx, error):
    #        if error is AttributeError or error is commands.errors.MissingRequiredArgument:
    #            return ctx.send(
    #                f"There was an error processing your request (Perhaps checks your command?) \n Details:{error}"
    #            )
    #        else:
    #            return ctx.send(
    #                f"There was an error processing your request \nDetails: {error}"
    #            )

    @commands.command(
        brief="Search for picture on SauceNAO, using Pixiv Database",
        description="Search for a picture in an embed or attachment, using the SauceNAO engine.\n\
                          Pixiv only as of now. Twitter is scary",
    )
    async def sauceplz(self, ctx):
        print(
            "@"
            + ctx.message.author.name
            + "#"
            + ctx.message.author.discriminator
            + " try to find sauce!"
        )
        async with ctx.channel.typing():
            if ctx.message.reference:
                if ctx.message.reference.resolved != None:
                    search_msg = ctx.message.reference.resolved
                    if search_msg.embeds.__len__() > 0:
                        for attachment in search_msg.embeds:
                            if attachment.image != None:
                                try:
                                    found = await find_sauce(attachment.url)
                                    # print(attachment.url)
                                    if found == None:
                                        await ctx.send(
                                            "I am sssorry, can't get your sauce :("
                                        )
                                        await ctx.send("Ask Buzzle why that is")
                                    else:
                                        try:
                                            att_embed = await self.construct_saucenao_embed_pixiv(
                                                found
                                            )
                                            await ctx.send(embed=att_embed)
                                        except (
                                            discord.errors.HTTPException,
                                            AttributeError,
                                        ) as e:
                                            print(e)
                                            await ctx.send(
                                                "Something went wrong and I can't look up your image."
                                            )
                                            await ctx.send(
                                                "Either it has been deleted or hidden by the author, or it isn't on Pixiv"
                                            )
                                except TypeError:
                                    await ctx.send("I couldn't find anything :(")
                    elif search_msg.attachments.__len__() > 0:
                        for attachment in search_msg.attachments:
                            if attachment.content_type.startswith("image"):
                                found = await find_sauce(attachment.url)
                                # print(attachment.url)
                                if found == None:
                                    await ctx.send(
                                        "I am sssorry, can't get your sauce :("
                                    )
                                    await ctx.send("Ask Buzzle why that is")
                                else:
                                    try:
                                        att_embed = (
                                            await self.construct_saucenao_embed_pixiv(
                                                found
                                            )
                                        )
                                        await ctx.send(embed=att_embed)
                                    except (
                                        discord.errors.HTTPException,
                                        AttributeError,
                                    ) as e:
                                        print(e)
                                        await ctx.send(
                                            "Something went wrong and I can't look up your image."
                                        )
                                        await ctx.send(
                                            "Either it has been deleted or hidden by the author, or it isn't on Pixiv"
                                        )
            else:
                await ctx.send("Please mention a message containing pasta!")

    @commands.command(
        brief="Search for picture on IQDB",
        description="Search for a picture in an embed or attachment, using the IQDB engine.\n\
                          Slower than SauceNAO, but has a higher search limit",
    )
    async def iqdb(self, ctx):
        print(
            "@"
            + ctx.message.author.name
            + "#"
            + ctx.message.author.discriminator
            + " try to find sauce on IQDB!"
        )
        async with ctx.channel.typing():
            if ctx.message.reference:
                if ctx.message.reference.resolved != None:
                    search_msg = ctx.message.reference.resolved
                    if search_msg.embeds.__len__() > 0:
                        for attachment in search_msg.embeds:
                            if attachment.image != None:
                                try:
                                    found = await self.construct_iqdb_embed(
                                        attachment.url
                                    )
                                    # print(attachment.url)
                                    if found == None:
                                        await ctx.send(
                                            "I am sssorry, can't get your sauce :("
                                        )
                                        await ctx.send("Ask Buzzle why that is")
                                    else:
                                        try:
                                            await ctx.send(embed=found)
                                        except (
                                            discord.errors.HTTPException,
                                            AttributeError,
                                        ) as e:
                                            print(e)
                                            await ctx.send(
                                                "Something went wrong and I can't look up your image."
                                            )
                                            await ctx.send(
                                                "Either it has been deleted or hidden by the author, or it isn't on Pixiv"
                                            )
                                        pass
                                except TypeError:
                                    await ctx.send("I couldn't find anything :(")
                    elif search_msg.attachments.__len__() > 0:
                        for attachment in search_msg.attachments:
                            if attachment.content_type.startswith("image"):
                                found = await self.construct_iqdb_embed(attachment.url)
                                if found == None:
                                    await ctx.send(
                                        "I am sssorry, can't get your sauce :("
                                    )
                                    await ctx.send("Ask Buzzle why that is")
                                else:
                                    try:
                                        await ctx.send(embed=found)
                                    except (
                                        discord.errors.HTTPException,
                                        AttributeError,
                                    ) as e:
                                        print(e)
                                        await ctx.send(
                                            "Something went wrong and I can't look up your image."
                                        )
                                        await ctx.send(
                                            "Either it has batt_embedeen deleted or hidden by the author, or it isn't on Pixiv"
                                        )
            else:
                await ctx.send("Please mention a message containing pasta!")

    @staticmethod
    async def construct_saucenao_embed_pixiv(attachment: SauceNaoResults):
        embed = discord.Embed(title="Sauce found!")
        embed.add_field(
            name="Similarity", value=f"{attachment.similarity}%", inline=False
        )
        if attachment.title:
            embed.add_field(name="Title", value=attachment.title, inline=False)
        if attachment.author_name:
            embed.add_field(
                name="Author",
                value=f"{attachment.author_name} - {attachment.author_url}",
                inline=False,
            )
        if attachment.source_url:
            embed.add_field(name="Source", value=attachment.source_url, inline=False)
        if attachment.index_name:
            embed.add_field(name="Index", value=attachment.index_name, inline=False)
        embed.set_thumbnail(url=attachment.thumbnail)
        if attachment.url:
            embed.url = attachment.url
        if attachment.urls:
            embed.url = attachment.urls[0]
        return embed

    @staticmethod
    async def construct_iqdb_embed(url: str):
        data = await get_sauce(url)
        if not data:
            return None
        embed = discord.Embed(title="Sauce found!")
        embed.url = data["link"]
        embed.set_thumbnail(url=data["thumbnail"])
        embed.add_field(name="Location", value=data["link"], inline=False)

        embed.add_field(name="Alt Text", value=data["alt_text"], inline=False)
        return embed


def setup(client):
    client.add_cog(SauceFinder(client))
