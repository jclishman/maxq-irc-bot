import sqlite3

# Connects to the database
database = sqlite3.connect('database.db')
database_cursor = database.cursor()

# Outputs all the rows
def output_rows_messages():
	database_cursor.execute("SELECT * FROM messages")

	for row in database_cursor.fetchall():
		print (row)

# Inserts a row into the messages table 
def insert_message(service, author, message, url):
	print (service + author, message, url)
	database_cursor.execute("INSERT INTO messages (service, author, message, url) VALUES(?,?,?,?)", [service, author, message, url])
	database.commit()

# Updates the PUBLISHED entry to 1
def update_after_publish(target_id):
	database_cursor.execute("UPDATE messages SET published = 1 WHERE id =" + str(target_id))
	database.commit()

# Gets the queue of messages that haven't been posted
def get_post_queue():
	database_cursor.execute("SELECT * FROM messages WHERE published = 0")

	return database_cursor.fetchall()

# Gets the accounts that the bot is following on Twitter
def get_following_twitter():
	database_cursor.execute("SELECT * FROM following WHERE twitter = 1")
	
	return database_cursor.fetchall()
	#return {x[0] for x in database_cursor.fetchall()}

