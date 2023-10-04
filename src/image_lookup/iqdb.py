import aiohttp, asyncio, logging
from bs4 import BeautifulSoup

iqdb_endpoint = "https://iqdb.org/?url="


async def get_sauce(url: str):
    """Lookup IQDB for an image by URL

    Args:
        url (str): The URL to the image

    Returns:
        object: A description of the result
    """
    timeout = aiohttp.ClientTimeout(total=30)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        res = await session.get(iqdb_endpoint + url)
        soup = BeautifulSoup(await res.read(), "html.parser")
        result_disp = soup.find("div", id="pages")
        logging.debug(result_disp)
        res = result_disp.find_all("table")
        res.remove(res[0])
        for _ in res:
            img_link = _.find("a")["href"]
            if img_link.startswith("//"):
                img_link = "https:" + img_link
            img_info = _.find("a").find("img")

            tds = _.find_all("td")
            logging.debug(tds)
            for td in tds:
                if "Safe" in td.text:
                    return {
                        "link": img_link,
                        "alt_text": img_info["alt"],
                        "thumbnail": "https://iqdb.org" + img_info["src"],
                    }
        return None


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    sauce = loop.run_until_complete(
        get_sauce("https://s1.zerochan.net/600/47/21/3166097.jpg")
    )
    logging.debug(sauce)
