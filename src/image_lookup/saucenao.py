from pysaucenao import SauceNao, SauceNaoIndexes, SauceNaoFilter
from pysaucenao.errors import SauceNaoError
from config_reader import GLOBAL_CONFIG as config
import asyncio, logging

indexes = SauceNaoIndexes()
indexes.add(SauceNaoIndexes.ALL)

saucer = SauceNao(
    api_key=config["Credentials"]["saucenao_key"],
    indexes=indexes,
    filter_level=SauceNaoFilter.POTENTIALLY_EXPLICIT,
    max_results=1,
)


async def find_sauce(url):
    """Look up image on SauceNao

    Args:
        url (str): The URL of the image

    Returns:
        BasicSauce: The first search result
    """
    logging.debug("Searching SauceNAO for image: " + url)
    try:
        results = await saucer.from_url(url)
        logging.debug(results)
        return results[0]
    except SauceNaoError as e:
        logging.critical(e)
        return None
    except IndexError:
        return None


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    sauce = loop.run_until_complete(
        find_sauce(
            "https://i.pximg.net/img-master/img/2021/04/21/18/00/47/89297449_p0_master1200.jpg"
        )
    )
    logging.debug(sauce)
