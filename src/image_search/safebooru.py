import random
import logging

import aiohttp
import discord
from bs4 import BeautifulSoup

from . import tf_scan

random_gen = random.SystemRandom()
endpoint = "https://safebooru.org/index.php?page=dapi&s=post&q=index&tags=rating:safe "


async def get_image(tags: str, bypass=False):
    """
    Search SafeBooru for images
    :param bypass: Bypass filters
    :param query: What to look for
    """
    global random_gen

    timeout = aiohttp.ClientTimeout(total=15)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        res = await session.get(endpoint + tags)

        soup = BeautifulSoup(await res.read(), features="xml")
        count = int(soup.find("posts")["count"])

        logging.debug(endpoint + tags)
        logging.debug(count)
        try:
            position = random_gen.randint(0, count - 1)
        except ValueError:
            return None
        for _ in range(3):
            if position < 100:
                try:
                    post = soup.find_all("post")[position]
                    logging.debug(position)

                    if not bypass:
                        if not (await tf_scan(post.get("file_url"))):
                            position = random_gen.randint(0, count - 1)
                            continue

                    embed = discord.Embed(title="Your random image!")
                    embed.set_image(url=post.get("file_url"))
                    embed.add_field(
                        name="Source", value=post.get("source") + " ", inline=False
                    )

                    embed.add_field(
                        name="Tags",
                        value="```\n" + post.get("tags").strip()[:1018] + "\n```",
                        inline=False,
                    )

                    return embed
                except IndexError:
                    return None
            else:
                page = int(position / 100)

                remote_res = await session.get(endpoint + tags + "&pid=" + str(page))

                remote_soup = BeautifulSoup(await remote_res.read(), features="xml")

                position = position % 100 - 1

                if position < 0:
                    position = 0

                post = remote_soup.find_all("post")[position]

                logging.debug(page)
                logging.debug(position)

                if not bypass:
                    if not (await tf_scan(post.get("file_url"))):
                        position = random_gen.randint(0, count - 1)
                        continue

                embed = discord.Embed(title="Your random image!")
                embed.set_image(url=post.get("file_url"))
                embed.add_field(
                    name="Source", value=post.get("source") + " ", inline=False
                )

                embed.add_field(
                    name="Tags",
                    value="```\n" + post.get("tags").strip()[:1018] + "\n```",
                    inline=False,
                )

                return embed
        return None


def convert_to_sb_tag(tags: list):
    """
    Convert a string to safebooru compatible tags
    :param tags: a list of tags
    :return: A string of safebooru tags
    """
    new_tags = []
    for tag in tags:
        tag = tag.lower().strip()
        tag = tag.replace(" ", "_")
        new_tags.append(tag)
    ret = " ".join(new_tags)
    logging.debug(ret)
    return ret


async def safebooru_random_img(tags: list, ch) -> discord.Embed:
    """
    Randomly get an image from specified tags
    :param tags: A list of tags
    :param ch: The Discord channel (So we can decide if it's SFW)
    :return: An embed ready to be sent
    """
    tags = convert_to_sb_tag(tags)

    if ch.type is not discord.ChannelType.private:
        emb = await get_image(tags, ch.is_nsfw())
    else:
        emb = await get_image(tags, True)
    if emb:
        return emb
    else:
        return None


if __name__ == "__main__":
    arg = "Ganyu (Genshin Impact) + Amber (Genshin Impact)"
    args = arg.split("+")

    logging.debug(safebooru_random_img(args).to_dict(), discord.ext.commands.Context())
    pass
