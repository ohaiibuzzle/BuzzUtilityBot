import configparser
import os
import logging

HAS_CONFIG = True

if not os.path.exists("runtime"):
    os.mkdir("runtime")
    os.mkdir("runtime/models")
    HAS_CONFIG = False

if not os.path.exists("runtime/config.cfg"):
    logging.critical("No config file found!")
    HAS_CONFIG = False

if not HAS_CONFIG:
    logging.critical("Please populate the /runtime directory with your credentials!")
    config = configparser.ConfigParser()
    config["Credentials"] = {
        "discord_key": "",
        "pixiv_key": "",
        "saucenao_key": "",
        "youtube_data_v3_key": "",
        "spotify_web_api_cid": "",
        "spotify_web_api_sec": "",
        "twitter_bearer_token": "",
        "zerochan_user_agent": "",
    }

    config["Dependancies"] = {
        "nsfw_model_path": "runtime/models/mobileNet.tflite",
        "nsfw_image_dim": "224",
        "nsfw_tflite_threads": "1",
        "redis_host": "redis://redis",
        "nitter_instances": "",
        "tweetwatch_wait_time": "60",
    }

    config["Features"] = {
        "blacklisted_features": "utils.nsfwRole",
        "log_level": "WARNING",
        "log_file": "",
        "prefix": ".",
    }

    with open("runtime/config.cfg", "w+") as configfile:
        config.write(configfile)
    exit(0)

if HAS_CONFIG:
    GLOBAL_CONFIG = configparser.ConfigParser()
    GLOBAL_CONFIG.read("runtime/config.cfg")