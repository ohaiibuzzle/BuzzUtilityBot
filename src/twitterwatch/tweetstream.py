import datetime
import pnytter
import asyncio


class TweetStreamer:
    def __init__(self, pnytter_instances: list, callback, wait_time=60):
        self.nitter_client = pnytter.Pnytter(
            nitter_instances=pnytter_instances
        )
        self.on_data_callback = callback
        self.streaming_task: asyncio.Task = None
        self.wait_time = wait_time

    async def stream(self, accounts: list):
        # print("Scraper started")
        latest_tweets = {}
        while True:
            today_utc = datetime.datetime.utcnow()
            tomorrow_utc = today_utc + datetime.timedelta(days=1)
            yesterday_utc = today_utc - datetime.timedelta(days=1)
            for account in accounts:
                # print(f"Checking {account}")
                if account not in latest_tweets:
                    latest_tweets[account] = []
                try:
                    tweets = self.nitter_client.get_user_tweets_list(
                        username=account,
                        filter_from=yesterday_utc,
                        filter_to=tomorrow_utc,
                    )
                    if tweets:
                        for tweet in tweets:
                            if tweet.tweet_id not in latest_tweets[account]:
                                await self.on_data_callback(tweet, account)
                        latest_tweets[account] = [
                            tweet.tweet_id for tweet in tweets
                        ]

                except Exception as e:
                    print(e)
            await asyncio.sleep(self.wait_time)

    def start(self, accounts: list):
        self.streaming_task = asyncio.create_task(self.stream(accounts))

    def stop(self):
        if self.streaming_task:
            self.streaming_task.cancel()
