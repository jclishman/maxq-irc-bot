from bot_logging import logger
from tweepy.streaming import StreamListener
import tweepy
import time
import html
import json
import sqlite3
import db

# Secret credentials :)
credentials = json.load(open('_config.json'))

# API Authentication
auth = tweepy.OAuthHandler(credentials["consumer_key"], credentials["consumer_secret"])
auth.set_access_token(credentials["access_token"], credentials["access_secret"])
api = tweepy.API(auth)

# Gets the list of users and their attributes from the database
users_list = db.get_following("twitter")

# Puts all the User IDs into a set for optimal performance
following = {x[1] for x in users_list}


# Tweet stream
class MyStreamListener(StreamListener):


    def on_data(self, data):

        # Converts the data into usable JSON
        data = json.loads(data)

        # Puts user attributes into this list if the tweeet is from somebody the bot is following
        # If the tweet isn't from someone the bot is following, set to None
        # For some reason the twitter API also tells you when someone deletes a tweet
        # If you try to get the needed properties from a deleted tweet, it throws a KeyError
        try:
            user_of_tweet = next((x for x in users_list if x[1] == data['user']['id_str']), None)

        except KeyError as e:
            user_of_tweet = None

        # Sends the tweet to the database
        def send_tweet_to_db(start_time):
            # Gets the full tweet text if it's concatenated by Twitter
            if "extended_tweet" in data:
                text = html.unescape(data['extended_tweet']['full_text'])

            # Gets the full retweet text if it's concatenated by Twitter
            elif "retweeted_status" in data and "extended_tweet" in data['retweeted_status']:
                rt_data = data['retweeted_status']
                text = "RT @%s: %s" % (rt_data['user']['screen_name'], html.unescape(rt_data['extended_tweet']['full_text']))

            # Not an extended tweet
            else:
                text = html.unescape(data['text'])
            
            # Logs raw JSON    
            #logger.info(json.dumps(data))
            tweet_url = make_url_from_tweet(data['user']['screen_name'], data['id_str'])
            db.insert_message('Twitter', data['user']['screen_name'], text, tweet_url, start_time)

        # Is the tweet from somebody the bot cares about?
        if user_of_tweet is not None:

            start_time = time.time()

            # Is it a retweet?             Is the retweet flag of the user set to 1?
            if "retweeted_status" in data and user_of_tweet[2] == 1:
                rt_data = data['retweeted_status']

                # Has the retweeted status been posted before?
                if db.get_tweet_posted(make_url_from_tweet(rt_data['user']['screen_name'], rt_data['id_str'])) == []:
                    send_tweet_to_db(start_time)

                # Yes it has, don't post it again
                else:
                   logger.info("Retweet has already been posted")

            # Is a reply?                  Is the reply flag of the user set to 1?
            elif data['in_reply_to_status_id'] is not None and user_of_tweet[3] == 1:
                send_tweet_to_db(start_time)

            # If it's a normal tweet
            elif "retweeted_status" not in data and data["in_reply_to_status_id"] is None:
                send_tweet_to_db(start_time)

    def on_error(self, status):
        if status == 420:
            return False

def run():

    # Makes the stream object
    myStreamListener = MyStreamListener()
    myStream = tweepy.Stream(auth, myStreamListener)

    # Streams tweets
    myStream.filter(follow=following)

def getID(username):
    try:
        user_data = api.get_user(screen_name=username)
        return user_data.id

    except tweepy.error.TweepError:
        return None

def make_url_from_tweet(screen_name, id_str):
    return 'https://twitter.com/%s/status/%s' % (screen_name, id_str)
