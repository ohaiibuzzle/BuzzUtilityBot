from pysaucenao import SauceNao
from pysaucenao.errors import SauceNaoException
import asyncio, configparser

config = configparser.ConfigParser()
config.read('runtime/config.cfg')

saucer = SauceNao(api_key=config['Credentials']['saucenao_key'], db=5)

async def find_sauce(url):
    """Look up image on SauceNao

    Args:
        url (str): The URL of the image

    Returns:
        BasicSauce: The first search result
    """
    try:
        results = await saucer.from_url(url)
        return results[0]
    except SauceNaoException as e:
        print(e)
        return None
    except IndexError:
        return None

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    sauce = loop.run_until_complete(find_sauce('https://i.pximg.net/img-master/img/2021/04/21/18/00/47/89297449_p0_master1200.jpg'))
    print(sauce)
    