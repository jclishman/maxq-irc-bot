import sqlite3
from bot_logging import logger

# Because the database is running on multiple threads, each method needs its own database connection and cursor

# Outputs all the rows
def output_rows_messages():
	database = sqlite3.connect('database.db')
	output_rows_cursor = database.cursor()
	output_rows_cursor.execute("SELECT * FROM messages")

	for row in output_rows_cursor.fetchall():
		print (row)

# Inserts a row into the messages table 
def insert_message(service, author, message, url):
	#print (service, author, message, url)
	
	try:
		database = sqlite3.connect('database.db')
		insert_message_cursor = database.cursor()
		insert_message_cursor.execute("INSERT INTO messages (service, author, message, url) VALUES(?,?,?,?)", [service, author, message, url])
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
def follow_account(username, user_id, retweets, replies, platform):

	try:
		database = sqlite3.connect('database.db')	
		follow_cursor = database.cursor()
		
		if platform == 'twitter':
			follow_cursor.execute("INSERT INTO following (username, twitter_id, retweets, replies) VALUES(?,?,?,?)", [username, user_id, retweets, replies])

		if platform == 'instagram':
			follow_cursor.execute("INSERT INTO following (username, instagram_) VALUES(?,?,?)", [username, user_id])

		database.commit()
	
	except sqlite3.OperationalError as e:
		logger.error(str(e))

def get_instagram_timestamp(username):

	try:
		database = sqlite3.connect('database.db')
		insta_get_timestamp_cursor = database.cursor()

		insta_get_timestamp_cursor.execute("SELECT instagram_timestamp_at FROM following WHERE username = '%s'" % username)

		return insta_get_timestamp_cursor.fetchone()[0]

	except sqlite3.OperationalError as e:
		logger.error(str(e))

def update_instagram_timestamp(username, timestamp):

	try:
		database = sqlite3.connect('database.db')
		insta_timestamp_cursor =  database.cursor()

		insta_timestamp_cursor.execute("UPDATE following SET instagram_timestamp_at = %s WHERE username = '%s'" % (timestamp, username))

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

	
		#print("> db.py - Got the following list")
		return get_following_cursor.fetchall()

	except sqlite3.OperationalError as e:
		logger.error(str(e))