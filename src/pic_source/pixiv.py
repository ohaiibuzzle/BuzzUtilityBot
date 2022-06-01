import asyncio
import configparser
import io
import random

import aiohttp
import discord
import pixivpy_async

random_source = random.SystemRandom()

timeout = aiohttp.ClientTimeout(total=15)

config = configparser.ConfigParser()
config.read("runtime/config.cfg")


async def px_getamount(query: str):
    """
    Get an (approximate) amount of pics from Pixiv
    """
    # https://www.pixiv.net/ajax/search/artworks/hu%20tao?word=hu tao&order=date_d&mode=all&p=1&s_mode=s_tag&type=all&lang=en
    async with aiohttp.ClientSession(timeout=timeout) as session:
        data = await (
            await session.get(
                "https://www.pixiv.net/ajax/search/artworks/"
                + query
                + "?s_mode=s_tag&type=all&lang=en"
            )
        ).json()
        return data["body"]["illustManga"]["total"]


async def get_image(query: str, bypass=False):
    """Get an image from Pixiv

    Args:
        query (str): The query to search for
        bypass (bool, optional): Bypass. Defaults to False.

    Returns:
        result: PixivPy illustration info
        image_data: the image, in a bytesIO format
    """
    async with pixivpy_async.PixivClient() as client:
        aapi = pixivpy_async.AppPixivAPI(client=client)
        aapi.set_accept_language("en-us")

        # print(query)
        try:
            total = await px_getamount(query)
        except TimeoutError:
            total = 30

        # print(total)

        if total > 1450:
            total = 1450

        global random_source

        await aapi.login(refresh_token=config["Credentials"]["pixiv_key"])

        # print(total)
        for _ in range(3):
            choice = random_source.randrange(total) - 1

            if choice < 0:
                choice = 0

            # print(choice)

            # res = await aapi.search_illust(query, offset=1450)

            # print(res)
            # print(res['illusts'].__len__())

            result = (await aapi.search_illust(query, offset=choice))["illusts"][0]

            if not bypass:
                if result["x_restrict"] != 0:
                    continue
                if result["sanity_level"] > 5:
                    continue
            # print(choice)
            raw_data = [
                x
                async for x in await aapi.down(
                    result["image_urls"]["large"], "https://app-api.pixiv.net/"
                )
            ]

            image_data = io.BytesIO(raw_data[0])
            return result, image_data

        return None


async def get_image_by_id(illust_id: int):
    """
    Get a Pixiv embed from a Pixiv Illustration ID
    :param illust_id: ID of a Pixiv illustration
    :return: a Pixiv Embed ready to be sent
    """
    async with pixivpy_async.PixivClient() as client:
        aapi = pixivpy_async.AppPixivAPI(client=client)
        aapi.set_accept_language("en-us")

        await aapi.login(refresh_token=config["Credentials"]["pixiv_key"])
        res = (await aapi.illust_detail(illust_id))["illust"]

        #print(res)

        if res["x_restrict"] != 0:
            return None
        if res["sanity_level"] > 5:
            return None

        raw_data = [
            x
            async for x in await aapi.down(
                res["image_urls"]["large"], "https://app-api.pixiv.net/"
            )
        ]

        image_data = io.BytesIO(raw_data[0])

        embed = discord.Embed(
            title=res["title"],
            url="https://www.pixiv.net/en/artworks/" + str(res["id"]),
        )
        fn = res["image_urls"]["large"].split("/")[-1]
        # print(fn)
        file = discord.File(image_data, filename=fn)
        embed.set_image(url="attachment://" + fn)

        embed.add_field(name="Title" + " ", value=res["title"], inline=False)

        embed.add_field(
            name="Author",
            value="{}, Pixiv ID: {}".format(res["user"]["name"], res["user"]["id"]),
            inline=False,
        )

        tag_str = ""
        if res["tags"].__len__() > 0:
            for tag in res["tags"]:
                if tag.translated_name != None:
                    tag_str += tag["translated_name"]
                    tag_str += ", "
                else:
                    tag_str += tag["name"]
                    tag_str += ", "
            tag_str = tag_str[:-2]
        else:
            tag_str = None

        embed.add_field(name="Tags", value=tag_str, inline=False)
        return embed, file


async def construct_pixiv_embed(query, channel):
    """
    Creates an embed for Pixiv
    :param query: A query string
    :param ch: The Discord channel (So we can decide if it's SFW)
    :return: An embed ready to be sent
    """
    if channel.type == discord.ChannelType.private:
        res, img = await get_image(query)
    else:
        res, img = await get_image(query, channel.is_nsfw())
    if res != None:
        embed = discord.Embed(
            title=res["title"],
            url="https://www.pixiv.net/en/artworks/" + str(res["id"]),
        )
        fn = res["image_urls"]["large"].split("/")[-1]
        # print(fn)
        file = discord.File(img, filename=fn)
        embed.set_image(url="attachment://" + fn)

        embed.add_field(name="Title" + " ", value=res["title"], inline=False)

        embed.add_field(
            name="Author",
            value="{}, Pixiv ID: {}".format(res["user"]["name"], res["user"]["id"]),
            inline=False,
        )

        tag_str = ""
        if res["tags"].__len__() > 0:
            for tag in res["tags"]:
                if tag.translated_name != None:
                    tag_str += tag["translated_name"]
                    tag_str += ", "
                else:
                    tag_str += tag["name"]
                    tag_str += ", "
            tag_str = tag_str[:-2]
        else:
            tag_str = None

        embed.add_field(name="Tags", value=tag_str, inline=False)
        return embed, file
    return None


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    print(loop.run_until_complete(get_image("ganyu")))
