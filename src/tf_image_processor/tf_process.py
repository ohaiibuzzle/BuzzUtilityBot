from os import listdir, environ
from os.path import isfile, join, exists, isdir, abspath

environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 

import numpy as np
import tensorflow as tf
from tensorflow import keras
import tensorflow_hub as hub
from PIL import Image
import requests
import asyncio

IMAGE_DIM = 224

def load_model(model_path):
    if model_path is None or not exists(model_path):
    	raise ValueError("saved_model_path must be the valid directory of a saved model to load.")
    
    model = tf.keras.models.load_model(model_path, custom_objects={'KerasLayer': hub.KerasLayer})
    return model

def load_image_array(array, image_size):
    image = tf.image.resize(np.asarray(array), image_size, preserve_aspect_ratio=False).numpy()
    image /= 255
    
    #np.savetxt('test.csv', image.reshape((3,-1)), delimiter=',')
    
    return image

def process_url(url: str):
    im = Image.open(requests.get(url, stream=True, timeout=15).raw).resize((IMAGE_DIM, IMAGE_DIM), Image.NEAREST)
    #im.show()
    image = keras.preprocessing.image.img_to_array(im)
    image = image[:,:,:3]
    image /= 255
    
    #np.savetxt('test.csv', image.reshape((3,-1)), delimiter=',')
    
    preds = model.predict(np.asarray([image]))
    
    preds_dict = {}
    for _, value in enumerate(preds[0]):
        preds_dict[categories[_]] = [value, colors[_]]
        
    return preds_dict

async def async_process_url(url:str):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, process_url, url)

model = load_model('./runtime/models/mobileNet/')
categories = ['(o･ω･o) (D)', '(o-_-o) (H)', '(ﾉ´ з `)ノ (N)', '(╬ Ò﹏Ó) (P)', '(°ㅂ°╬) (S)']
colors = [0xD53113, 0x5B17B1, 0x2299B8, 0x6B1616, 0x1EB117]

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    url = 'https://s1.zerochan.net/Rosaria.600.3281202.jpg'
    predicts = loop.run_until_complete(async_process_url(url))

    print(url)
    sorted = {k: v for k, v in sorted(predicts.items(), key=lambda item: item[1], reverse=True)}
    for _ in sorted:
        print(_ + ' --> ' + str(format(sorted[_][0] * 100, '.2f'))+'%')

    print('==> ' + list(sorted.keys())[0].capitalize())