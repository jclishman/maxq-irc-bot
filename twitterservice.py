from tweepy.streaming import StreamListener
import tweepy
import time
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

        # Sends the tweet to the database    Username                 Message            URL
        def send_tweet_to_db(start_time):
            db.insert_message('Twitter', data['user']['screen_name'], data['text'],
                              'https://twitter.com/%s/status/%s' % (data['user']['screen_name'], data['id_str']),
                              start_time)

        # Is the tweet from somebody the bot cares about?
        if user_of_tweet != None:
            start_time = time.time()

            # Is it a retweet?             Is the retweet flag of the user set to 1?
            if "retweeted_status" in data and user_of_tweet[2] == 1:
                send_tweet_to_db(start_time)

            # Is a reply?                  Is the reply flag of the user set to 1?
            if data['in_reply_to_status_id'] is not None and user_of_tweet[3] == 1:
                send_tweet_to_db(start_time)

            # If it's a normal tweet
            elif "retweeted_status" not in data:
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
