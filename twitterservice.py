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
api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

# Gets the list of users and their attributes from the database
users_list = db.get_following("twitter")

# Puts all the User IDs into a set for optimal performance
following = {x[1] for x in users_list}


# Tweet stream
class MyStreamListener(StreamListener):

    def on_status(self, status):

        #print(status.text)
        #print(json.dumps(status._json))

        # Converts the data into usable JSON
        data = status._json


        # Puts user attributes into this list if the tweet is from somebody the bot is following
        # If the tweet isn't from someone the bot is following, set to None
        # For some reason the twitter API also tells you when someone deletes a tweet
        # If you try to get the needed properties from a deleted tweet, it throws a KeyError
        try:
            user_of_tweet = next((x for x in users_list if x[1] == data['user']['id_str']), None)
        except KeyError as e:
            return

        if user_of_tweet is None:
            # Not following this user, do nothing.
            return

        start_time = time.time()

        # Is it a retweet?             Is the retweet flag of the user set to 1?
        if "retweeted_status" in data and user_of_tweet[2] == 1:
            rt_data = data['retweeted_status']

            # Has the retweeted status already been posted?
            # No, post it
            if not has_tweet_been_posted(rt_data['user']['screen_name'], rt_data['id_str']):
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
                usernames_to_modify = ['@elonmusk', '@SpaceX']

                for username in usernames_to_modify:
                    ZWJ = "‍"

                    # Inserts a Zero Width Joiner
                    username_zwj = username[:2] + ZWJ + username[2:]
                    reply_data['full_text'] = reply_data['full_text'].replace(username, username_zwj)

                reply_data['text'] = reply_data['full_text']

                # Don't send the ID of the reply tweet
                reply_data['id_str'] = None

                send_tweet_to_db(reply_data, start_time)
                time.sleep(0.5)
                send_tweet_to_db(data, start_time)

            # Yes, don't send it again
            else:
                send_tweet_to_db(data, start_time)
                logger.info("Parent tweet already posted")

        # If it's a normal tweet
        elif "retweeted_status" not in data and data["in_reply_to_status_id"] is None:
            send_tweet_to_db(data, start_time)

    # Trying to find out what's causing the random Twitter crashes
    def on_error(self, status):
        if status == 420:
            logger.error("----RATELIMITED ERROR 420----")
            return False
        else:
            logger.error("----ERROR----")

    #def on_exception(self, exception):
        #logger.error("-----ERROR-----")
        #logger.error(exception)
        
        #db.insert_message('Twitter', 'Twitter Thread', 'jclishman: Check logs', '', time.time())
        #return True

def run():

    logger.info("Starting Twitter Stream...")
    # Makes the stream object
    myStreamListener = MyStreamListener()
    myStream = tweepy.Stream(auth, myStreamListener)

    # Streams tweets
    try:
        myStream.filter(follow=following, stall_warnings=True)
    except Exception as e:
        logger.error("-----CAUGHT ERROR-----")
        logger.error(str(e))
        logger.error("-----ATTEMPTING RECONNECT-----")

        run()

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
    return f"https://twitter.com/{screen_name}/status/{id_str}"

def has_tweet_been_posted(screen_name, id_str):
    return db.get_tweet_posted(make_url_from_tweet(screen_name, id_str)) != []

def send_tweet_to_db(tweet_data, start_time):
    """Sends the tweet to the database"""

    screen_name = tweet_data['user']['screen_name']

    # Checks if the tweet is a parent to a reply, which won't have an ID
    if tweet_data['id_str'] is not None:
        tweet_url = make_url_from_tweet(tweet_data['user']['screen_name'], tweet_data['id_str'])
    else:
        tweet_url = ''

    rt_prefix = ""

    # If this is a retweet, use the content of the original tweet.
    if "retweeted_status" in tweet_data:
        tweet_data = tweet_data['retweeted_status']
        rt_prefix =  f"RT @{tweet_data['user']['screen_name']}: "

    if "extended_tweet" in tweet_data:
        tweet_data = tweet_data['extended_tweet']

    # "full_text" isn't cut off for tweets >140 chars, but may not exist.
    tweet_text = tweet_data.get("full_text") or tweet_data['text']

    # Replace twitter's redirect shortlinks with the original URL;
    #  makes it easier to see what's being linked to and avoids tracking.
    for url in tweet_data['entities']['urls']:
        tweet_text.replace(url['url'], url['expanded_url'])

    # Replace media (image/video) shortlinks with direct links to the file,
    #  so users don't have to go through Twitter's JS-laden tweet page.
    if "extended_entities" in tweet_data:
        for media in tweet_data['extended_entities']['media']:
            real_url = media['media_url_https']
            # Get full resolution image. This scheme is "deprecated", but much shorter
            #  than the recommended `?format=jpg&name=orig` and still works.
            if real_url.endswith(".jpg"):
                real_url += ":orig"
            tweet_text.replace(media['url'], media['media_url_https'])

    text = (rt_prefix + html.unescape(tweet_text)).replace("\n", " ")

    # Logs raw JSON
    #logger.info(json.dumps(data))

    db.insert_message('Twitter', screen_name, text, tweet_url, start_time)
