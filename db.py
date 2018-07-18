from bot_logging import logger
import sqlite3


# Because the database is running on multiple threads, each method needs its own database connection and cursor

# Inserts a row into the messages table
def insert_message(service, author, message, url, start_time):
    # print (service, author, message, url)

    try:
        database = sqlite3.connect('database.db')
        insert_message_cursor = database.cursor()
        insert_message_cursor.execute(
            "INSERT INTO messages (service, author, message, url, start_time) VALUES(?,?,?,?,?)",
            [service, author, message, url, start_time])
        database.commit()

    except sqlite3.OperationalError as e:
        logger.error(str(e))


# Updates the PUBLISHED entry to 1
def update_after_publish(target_id):

    try:
        database = sqlite3.connect('database.db')
        update_cursor = database.cursor()
        update_cursor.execute("UPDATE messages SET published = 1 WHERE id =%s" % str(target_id))
        database.commit()

    except sqlite3.OperationalError as e:
        logger.error(str(e))


# Follows accounts
def follow_account(username, user_id, retweets, replies):
    try:
        database = sqlite3.connect('database.db')
        follow_cursor = database.cursor()

        follow_cursor.execute("INSERT INTO following (username, twitter_id, retweets, replies) VALUES(?,?,?,?)",
                              [username, user_id, retweets, replies])
        logger.info('Added to DB')
        database.commit()

    except sqlite3.OperationalError as e:
        logger.error(str(e))


# Unfollows accounts
def unfollow_account(user_id):
    try:
        database = sqlite3.connect('database.db')
        unfollow_cursor = database.cursor()

        unfollow_cursor.execute("DELETE FROM following WHERE twitter_id = %s" % user_id)
        database.commit()
        logger.info('Deleted from DB')

    except sqlite3.OperationalError as e:
        logger.error(str(e))


# Sets flags
def set_flags(user_id, retweets, replies):
    try:
        database = sqlite3.connect('database.db')
        set_flags_cursor = database.cursor()

        set_flags_cursor.execute(
            "UPDATE following SET retweets = %i, replies = %i WHERE twitter_id = %s" % (retweets, replies, user_id))
        logger.info('Updated DB flags')
        database.commit()
    except sqlite3.OperationalError as e:
        logger.error(str(e))


def get_instagram_timestamp(username):
    try:
        database = sqlite3.connect('database.db')
        insta_get_timestamp_cursor = database.cursor()

        insta_get_timestamp_cursor.execute(
            "SELECT instagram_timestamp_at FROM following WHERE username = '%s'" % username)

        return insta_get_timestamp_cursor.fetchone()[0]

    except sqlite3.OperationalError as e:
        logger.error(str(e))


def update_instagram_timestamp(username, timestamp):
    try:
        database = sqlite3.connect('database.db')
        insta_timestamp_cursor = database.cursor()

        insta_timestamp_cursor.execute(
            "UPDATE following SET instagram_timestamp_at = %s WHERE username = '%s'" % (timestamp, username))

        database.commit()

    except sqlite3.OperationalError as e:
        logger.error(str(e))


# Gets the queue of messages that haven't been posted
def get_post_queue():
    try:
        database = sqlite3.connect('database.db')
        post_cursor = database.cursor()
        post_cursor.execute("SELECT * FROM messages WHERE published = 0")

        return post_cursor.fetchall()

    except sqlite3.OperationalError as e:
        logger.error(str(e))


# Gets the accounts that the bot is following
def get_following(platform):
    try:
        database = sqlite3.connect('database.db')
        get_following_cursor = database.cursor()

        if platform == 'twitter': get_following_cursor.execute(("SELECT * FROM following WHERE twitter_id != 0"))
        if platform == 'instagram': get_following_cursor.execute(("SELECT * FROM following WHERE instagram != 0"))

        # print("> db.py - Got the following list")
        return get_following_cursor.fetchall()

    except sqlite3.OperationalError as e:
        logger.error(str(e))


# Get whether or not a tweet has been posted
def get_tweet_posted(tweet_url):
    try:
        database = sqlite3.connect('database.db')
        get_tweet_posted_cursor = database.cursor()

        get_tweet_posted_cursor.execute("SELECT id FROM messages WHERE url='%s'" % tweet_url)

        return get_tweet_posted_cursor.fetchall()

    except sqlite3.OperationalError as e:
        logger.error(str(e))

        