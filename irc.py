# TODO:
# Instagram error handling
# IRC Commands (Maybe use a config instead?)
# Separate logic for EsperNet and SnooNet
# "Launch mode" (just show tweets from spacex/elon)
# New name

from bot_logging import logger
import twitterservice, instagramservice, redditservice, db
import socket, ssl
import threading
import json
import time
import os

logger.info('Now Entering MaxQ...')

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

HOST = 'irc.esper.net'
#HOST = 'irc.snoonet.org'
PORT = 6697
NICK = 'MaxQ'
admin = 'jclishman'
channels = ['#spacex']

# Secret credentials :)
credentials = json.load(open('_secret.json'))
password = credentials['nickserv_password']

# Responds to server pings
def pong(text):
    logger.debug('PONG' + text.split()[1])
    irc.send(parse('PONG ' + text.split()[1]))

# Makes things human-readable
def parse(string): return bytes(string + '\r\n', 'UTF-8')

# Sends messages
def send_message(message):
	for channel in channels:
		irc.send(parse('PRIVMSG ' + channel + ' :' + message))

def restart_irc():
	logger.info('Restarting...')
	os.system('start cmd /c irc.py')
	time.sleep(5)
	irc.send(parse('QUIT :Be right back!'))
	exit()

# Estabilishes a secure SSL connection
s.connect((HOST, PORT))
irc = ssl.wrap_socket(s)

logger.info('Connecting...')

time.sleep(5)

# Tells the server who it is
irc.send(parse('USER ' + NICK + ' ' + NICK + ' ' + NICK + ' :Bot'))
irc.send(parse('NICK ' + NICK))
logger.info('Server Ident')

time.sleep(2)

# Responds to the initial server ping on connection
has_responded_to_ping = False

while not has_responded_to_ping:
    text=irc.recv(1024).decode('UTF-8').strip('\r\n')

    if text.find('PING') != -1:
    	pong(text)
    	has_responded_to_ping = True

time.sleep(2)

# Identifies nickname
irc.send(parse(('NickServ IDENTIFY %s %s\n' % (NICK, password))))
logger.info('NickServ Ident')

# Joins channel(s)
for channel in channels:

	irc.send(('JOIN {}\n').format(channel).encode())
	time.sleep(2)

# Threading
def twitter_thread():
	logger.info('Starting Twitter Thread')
	twitterservice.run()

def insta_thread():
	logger.info('Starting Instragram Thread')
	instagramservice.run()

def reddit_thread():
	logger.info('Starting Reddit Thread')
	redditservice.run()

twitter = threading.Thread(name='Twitter_Thread', target=twitter_thread)
insta = threading.Thread(name='Instagram_Thread', target=insta_thread)
reddit = threading.Thread(name='Reddit_Thread', target=reddit_thread)

twitter.daemon = True
insta.daemon = True
reddit.daemon = True

twitter.start()
insta.start()
reddit.start()

# Reads messages
# setBlocking needs to be False to allow for the passive sending of messages
irc.setblocking(False)
while True:
	irc_stream = None

	try:
		irc_stream = irc.recv(1024).decode('UTF-8')

	except OSError as e:
		#print('No data')
		time.sleep(0.05)

	if irc_stream is not None: logger.info(irc_stream)

	# Sends server ping
	if irc_stream is not None and irc_stream.find('PING') != -1:
		pong(text)
	
	#print(time.ctime())
	if irc_stream is not None and irc_stream.find('PRIVMSG') != -1:

		message_author = irc_stream.split('!',1)[0][1:]
		message_channel = irc_stream.split('PRIVMSG',1)[1].split(':', 1)[0].lstrip()
		message_contents = irc_stream.split('PRIVMSG',1)[1].split(':',1)[1]

		#Debugging
		#logger.info(irc_stream)
		logger.info('Author: ' + message_author)
		logger.info('Channel: ' + message_channel)
		logger.info('Content: ' + message_contents)

		# Admins can make the bot quit
		if message_author == admin and message_contents.rstrip() == 'restart':
			restart_irc()
			os.system('exit')
		elif message_author == admin and message_contents.rstrip() == 'quit':
			irc.send(parse('QUIT :HTTP Error 418 - Stuck in orbit between Earth and Mars.'))
			logger.info('Exiting')
			exit()

	for row in db.get_post_queue():

		# Assembles and sends the IRC message
		# Platform-specific formatting
		if row[1] != 'Reddit': 
			send_message('[%s] @%s wrote: %s %s' % (row[1], row[2], row[3].replace('\n', ' '), row[4]))
			logger.info('[%s] @%s wrote: %s %s' % (row[1], row[2], row[3].replace('\n', ' '), row[4]))
		
		else: 
			send_message('[%s] %s %s' % (row[1], row[3], row[4]))
			logger.info('[%s] %s %s' % (row[1], row[3], row[4]))

		# Sends how long it took from tweet creation to irc message (debug)
		logger.info('Post #' + str(row[0]) + ', Took ' + str(round(time.time() - row[6], 5)) + 's\n')
		#print(str(round(time.time() - start_time, 5)), file=open('output.txt', 'a'))
		
		# Anti-bot spam
		time.sleep(1)
		
		# Updates the database after it posts something
		db.update_after_publish(row[0])


irc.close()

