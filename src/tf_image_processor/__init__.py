try:
    from .tf_process import async_process_url
except (ValueError, ModuleNotFoundError) as e:
    print("Model Error: " + str(e))
    print("ML features will be disabled")

    async def async_process_url(url: str):
        return {}
