try:
    from tf_image_processor.tf_process import async_process_url
except ValueError:
    print("Model Error")

    async def async_process_url(url: str):
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
            print("Model Error")
            return True
        print(res)
        if res["(o-_-o) (H)"][0] >= 0.59:
            print("Model detected Hentai content")
            return False
        if res["(╬ Ò﹏Ó) (P)"][0] >= 0.5:
            print("Model detected pornographic content")
            return False
        if res["(°ㅂ°╬) (S)"][0] >= 0.5:
            print("Model detected sexy content")
            return False
        return True
