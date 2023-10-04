import datetime
import pnytter
import asyncio
import logging


class TweetStreamer:
    def __init__(self, pnytter_instances: list, callback, wait_time=60):
        self.nitter_client = pnytter.Pnytter(
            nitter_instances=pnytter_instances
        )
        self.on_data_callback = callback
        self.streaming_task: asyncio.Task = None
        self.wait_time = wait_time
        self.latest_tweets = {}

        
    async def stream(self, accounts: list):
        while True:
            logging.debug(f"Waiting {self.wait_time} seconds between each fetch")
            await asyncio.sleep(60)
            logging.debug("Fetching...")
            await self.fetch(accounts)

    async def fetch(self, accounts: list):
        today_utc = datetime.datetime.utcnow()
        tomorrow_utc = today_utc + datetime.timedelta(days=1)
        yesterday_utc = today_utc - datetime.timedelta(days=1)
        for account in accounts:
            logging.debug(f"Checking {account}")
            if account not in self.latest_tweets:
                self.latest_tweets[account] = []
            try:
                tweets = self.nitter_client.get_user_tweets_list(
                    username=account,
                    filter_from=yesterday_utc,
                    filter_to=tomorrow_utc,
                )
                profile = self.nitter_client.find_user(account)
                if tweets:
                    for tweet in tweets:
                        if tweet.tweet_id not in self.latest_tweets[account]:
                            await self.on_data_callback(tweet, profile)
                    self.latest_tweets[account] = [
                        tweet.tweet_id for tweet in tweets
                    ]

            except Exception as e:
                logging.critical(e)

    def start(self, accounts: list):
        loop = asyncio.get_event_loop()
        self.streaming_task = loop.create_task(self.stream(accounts))

    def stop(self):
        if self.streaming_task:
            self.streaming_task.cancel()
