import logging

try:
    from .tf_process import async_process_url
except (ValueError, ModuleNotFoundError) as e:
    logging.critical("Model Error: " + str(e))
    logging.critical("ML features will be disabled")

    async def async_process_url(url: str):
        return {}
