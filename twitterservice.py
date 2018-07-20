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
        def send_tweet_to_db(tweet_data, start_time):

            # Gets the full tweet text if it's concatenated by Twitter
            if "extended_tweet" in tweet_data:
                text = html.unescape(tweet_data['extended_tweet']['full_text'])

            # Gets the full retweet text if it's concatenated by Twitter
            elif "retweeted_status" in tweet_data and "extended_tweet" in tweet_data['retweeted_status']:
                rt_data = tweet_data['retweeted_status']
                text = "RT @%s: %s" % (rt_data['user']['screen_name'], html.unescape(rt_data['extended_tweet']['full_text']))

            # Not an extended tweet
            else:
                text = html.unescape(tweet_data['text'])
            
            # Logs raw JSON    
            #logger.info(json.dumps(data))

            # Checks if the tweet is a parent to a reply, which won't have an ID
            if tweet_data['id_str'] is not None:
                tweet_url = make_url_from_tweet(tweet_data['user']['screen_name'], tweet_data['id_str'])
            else:
                tweet_url = ''

            db.insert_message('Twitter', tweet_data['user']['screen_name'], text, tweet_url, start_time)

        # Is the tweet from somebody the bot cares about?
        if user_of_tweet is not None:

            start_time = time.time()

            # Is it a retweet?             Is the retweet flag of the user set to 1?
            if "retweeted_status" in data and user_of_tweet[2] == 1:
                rt_data = data['retweeted_status']

                # Has the retweeted status already been posted?
                # No, post it
                if not has_tweet_been_posted(data['user']['screen_name'], data['id_str']):
                    send_tweet_to_db(data, start_time)

                # Yes, don't post it
                else:
                   logger.info("Retweet has already been posted")

            # Is a reply?                  Is the reply flag of the user set to 1?
            elif data['in_reply_to_status_id'] is not None and user_of_tweet[3] == 1:
                
                reply_data = get_status(data['in_reply_to_status_id'])

                # Has the parent tweet to the reply been posted already?
                # No, send it as context
                if not has_tweet_been_posted(reply_data['user']['screen_name'], reply_data['id_str']):

                    # Avoid IRC double pings
                    usernames_to_remove = ['@elonmusk', '@SpaceX', '@' + data['user']['screen_name']]
                    
                    for username in usernames_to_remove:
                        reply_data['full_text'] = reply_data['full_text'].replace(username, '')

                    reply_data['text'] = reply_data['full_text']

                    # Don't send the ID of the reply tweet
                    reply_data['id_str'] = None

                    send_tweet_to_db(reply_data, start_time)
                    time.sleep(0.5)
                    send_tweet_to_db(data, start_time)

                # Yes, don't send it again
                else:
                    send_tweet_to_db(data, start_time)

            # If it's a normal tweet
            elif "retweeted_status" not in data and data["in_reply_to_status_id"] is None:
                send_tweet_to_db(data, start_time)

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

def get_status(id):
    try:
        status_obj = api.get_status(id, tweet_mode='extended')
        return status_obj._json
    
    except tweepy.error.TweepError as e:
        return str(e)

def make_url_from_tweet(screen_name, id_str):
    return 'https://twitter.com/%s/status/%s' % (screen_name, id_str)

def has_tweet_been_posted(screen_name, id_str):
    return db.get_tweet_posted(make_url_from_tweet(screen_name, id_str)) != []
