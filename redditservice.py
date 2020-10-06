from bot_logging import logger
import json
import praw
import time
import db

# Secret credentials :)
credentials = json.load(open('_config.json'))

reddit = praw.Reddit(client_id=credentials["reddit_id"], client_secret=credentials["reddit_secret"], user_agent = "MaxQ IRC Bot by u/jclishman")

subreddit = reddit.subreddit('SpaceX')


def run():
    last_post_time = time.time()

    while True:

        try:

            for submission in subreddit.new(limit=1):

                post_time = submission.created_utc

                if post_time > last_post_time:
                    start_time = time.time()

                    title = submission.title
                    author = submission.author
                    url = submission.shortlink

                    if submission.is_self:
                        post_type = 'text'
                    else:
                        post_type = 'link'

                    message = ('New %s post in r/%s by u/%s: "%s"' % (post_type, subreddit, author, title))
                    # print(message)
                    db.insert_message('Reddit', '', message, url, start_time)
                    last_post_time = post_time

            time.sleep(2)

        except Exception as e:
            logger.error(str(e))
