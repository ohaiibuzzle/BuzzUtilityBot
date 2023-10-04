import logging

try:
    from image_analyze.tf_process import async_process_url
except (ValueError, ModuleNotFoundError) as e:
    logging.critical("Model Error: " + str(e))
    logging.critical("ML features will be disabled")

    async def tf_scan(url: str):
        return True

else:

    async def tf_scan(url: str):
        """
        Use TensorFlow to scan the image against an ML model.
        Warning: If TF fails, it is ignored, so make sure either the tag filter is on or you may end up with things in your SFW channels
        :param url: an URL to scan
        """
        try:
            res = await async_process_url(url)
        except ValueError:
            logging.critical("Model Error")
            return True
        logging.debug(res)
        if res["(o-_-o) (Hentai)"][0] >= 0.5:
            logging.info("Model detected Hentai content")
            return False
        if res["(╬ Ò﹏Ó) (Porn)"][0] >= 0.5:
            logging.info("Model detected pornographic content")
            return False
        if res["(°ㅂ°╬) (Sexy)"][0] >= 0.5:
            logging.info("Model detected sexy content")
            return False
        return True
