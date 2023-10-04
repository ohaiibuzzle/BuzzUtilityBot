from contextlib import redirect_stderr
from os import environ
from os.path import exists
from traceback import print_tb

environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

import asyncio
import configparser

import numpy as np
import requests
import tflite_runtime.interpreter as tflite
from PIL import Image
import logging

# Read the runtime config
config = configparser.ConfigParser()
config.read("runtime/config.cfg")
model_path = config["Dependancies"]["nsfw_model_path"]
IMAGE_DIM = int(config["Dependancies"]["nsfw_image_dim"])
TFLITE_THREADS = int(config["Dependancies"]["nsfw_tflite_threads"])

try:
    CURRENT_UA = requests.get("https://www.useragents.me/api").json()["data"][0]["ua"]
except Exception:
    CURRENT_UA = "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0"
logging.info("TF: Loading NSFW Model. This may take a while...")
model_interpreter = tflite.Interpreter(
    model_path=model_path, num_threads=TFLITE_THREADS
)
model_interpreter.allocate_tensors()
input_details = model_interpreter.get_input_details()
output_details = model_interpreter.get_output_details()
categories = [
    "(o･ω･o) (Drawing)",
    "(o-_-o) (Hentai)",
    "(ﾉ´ з `)ノ (Neutral)",
    "(╬ Ò﹏Ó) (Porn)",
    "(°ㅂ°╬) (Sexy)",
]
colors = [0xD53113, 0x5B17B1, 0x2299B8, 0x6B1616, 0x1EB117]


def img_to_array(img):
    """
    Converts a PIL Image instance to a Numpy array.
    (Yes, this is, as you might have suspected, stolen from Keras. Thanks, Keras!)
    Args:
        img (PIL.Image): PIL Image instance.
    Returns:
        np.array: Numpy array.
    """
    x = np.asarray(img, dtype="float32")
    if len(x.shape) == 3:
        pass
    elif len(x.shape) == 2:
        x = x.reshape((x.shape[0], x.shape[1], 1))
    else:
        raise ValueError("Unsupported image shape: %s" % (x.shape,))
    return x


def process_url(url: str):
    """Analyzes an image from an URL using a model

    Args:
        url (str): The URL to the image

    Returns:
        dict: A dictionary describing the results
    """
    HEADERS = {
        "User-Agent": CURRENT_UA,
    }
    im = Image.open(requests.get(url, stream=True, headers=HEADERS, timeout=15).raw)
    im = im.resize((IMAGE_DIM, IMAGE_DIM), resample=0)
    if im.mode != "RGB":
        im = im.convert("RGB")

    # im.show()
    image = img_to_array(im)
    image /= 255

    # np.savetxt('test.csv', image.reshape((3,-1)), delimiter=',')

    model_interpreter.set_tensor(input_details[0]["index"], np.asarray([image]))
    model_interpreter.invoke()
    preds = model_interpreter.get_tensor(output_details[0]["index"])

    preds_dict = {}
    for _, value in enumerate(preds[0]):
        preds_dict[categories[_]] = [value, colors[_]]

    return preds_dict


async def async_process_url(url: str):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, process_url, url)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    url = "https://media.discordapp.net/attachments/807448656763944960/991395165153546400/FB_IMG_1656166673189.jpg"
    predicts = loop.run_until_complete(async_process_url(url))

    logging.debug(url)
    sorted = {
        k: v
        for k, v in sorted(predicts.items(), key=lambda item: item[1], reverse=True)
    }
    for _ in sorted:
        logging.debug(_ + " --> " + str(format(sorted[_][0] * 100, ".2f")) + "%")

    logging.debug("==> " + list(sorted.keys())[0].capitalize())
