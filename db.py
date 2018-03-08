import sqlite3

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
	print (service, author, message, url)
	
	try:
		database = sqlite3.connect('database.db')
		insert_message_cursor = database.cursor()
		insert_message_cursor.execute("INSERT INTO messages (service, author, message, url) VALUES(?,?,?,?)", [service, author, message, url])
		database.commit()

	except sqlite3.OperationalError as e:
		print("[ERROR] " + str(e))

# Updates the PUBLISHED entry to 1
def update_after_publish(target_id):

	try:
		database = sqlite3.connect('database.db')
		update_cursor = database.cursor()
		update_cursor.execute("UPDATE messages SET published = 1 WHERE id =%s" % str(target_id))
		database.commit()

	except sqlite3.OperationalError as e:
		print("[ERROR] " + str(e))

# Follows accounts
def follow_account(username, user_id, retweets, replies, platform):

	try:
		database = sqlite3.connect('database.db')	
		follow_cursor = database.cursor()
		
		if platform == 'twitter':
			follow_cursor.execute("INSERT INTO following (username, user_id, retweets, replies, twitter) VALUES(?,?,?,?,?)", [username, user_id, retweets, replies, 1])

		if platform == 'instagram':
			follow_cursor.execute("INSERT INTO following (username, user_id, instagram) VALUES(?,?,?)", [username, user_id, 1])

		database.commit()

	except:
		print("ERROR")

# Gets the queue of messages that haven't been posted
def get_post_queue():

	try:
		database = sqlite3.connect('database.db')
		post_cursor = database.cursor()
		post_cursor.execute("SELECT * FROM messages WHERE published = 0")

		return post_cursor.fetchall()

	except sqlite3.OperationalError as e:
		print("[ERROR] " + str(e))

# Gets the accounts that the bot is following
def get_following(platform):

	try:
		database = sqlite3.connect('database.db')
		get_following_cursor = database.cursor()
		get_following_cursor.execute(("SELECT * FROM following WHERE %s = 1") % platform)
	
		print("> db.py - Got the following list")
		return get_following_cursor.fetchall()

	except sqlite3.OperationalError as e:
		print("[ERROR] " + str(e))