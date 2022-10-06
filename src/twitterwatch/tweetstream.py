import tweepy
import tweepy.errors
import time
from tweepy.asynchronous import AsyncStreamingClient


class TweetStreamer(AsyncStreamingClient):
    def __init__(self, bearer_token, on_tweet_handler):
        super().__init__(bearer_token=bearer_token)
        self.users = []
        self.on_tweet_handler = on_tweet_handler

    async def update_rules(self):
        # Remove all rules
        try:
            ids = [rule_ids.id for rule_ids in (await self.get_rules()).data]
        except TypeError:
            ids = []

        if len(ids) > 0:
            await self.delete_rules(ids=ids)

        if self.users is None or len(self.users) == 0:
            return

        # Filter for users: (from: user1 OR from: user2 OR from: user3)
        user_filter = " OR ".join(f"from:{user}" for user in self.users)

        await self.add_rules(tweepy.StreamRule(value=user_filter))

        # dump the rule from the API
        # rules = await self.get_rules()
        # print(rules)
        # print("Rules updated")
        return

    async def on_data(self, raw_data):
        # print(raw_data)
        await super().on_data(raw_data)

    async def on_tweet(self, tweet):
        # print(f"Incoming tweet: {tweet.data}")
        await self.on_tweet_handler(tweet)

    async def on_errors(self, errors):
        print(f'{time.strftime("%Y-%m-%d %H:%M:%S")}: ', end="", flush=True)
        return await super().on_errors(errors)

    async def on_request_error(self, status_code):
        print(f'{time.strftime("%Y-%m-%d %H:%M:%S")}: ', end="", flush=True)
        return await super().on_request_error(status_code)

    async def on_exception(self, exception):
        print(f'{time.strftime("%Y-%m-%d %H:%M:%S")}: ', end="", flush=True)
        return await super().on_exception(exception)
