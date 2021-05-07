from saucenao_api import SauceNao
from saucenao_api.errors import SauceNaoApiError, ShortLimitReachedError
from saucenao_api.params import DB, Hide, BgColor

key=''
with open('saucenao.key', 'r') as keyfile:
    key = keyfile.readline()

saucer = SauceNao(key, db=DB.Pixiv_Images)

def find_sauce(url):
    try:
        results = saucer.from_url(url)
        return results[0].urls[0]
    except SauceNaoApiError as e:
        print(e)
        return None

if __name__ == '__main__':
    print(find_sauce('https://i.pximg.net/img-master/img/2021/04/21/18/00/47/89297449_p0_master1200.jpg'))