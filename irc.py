# Todo
# Two threads running at once (Instagram)
# IRC Commands
# Separate logic for EsperNet and SnooNet
# Get NickServ to work properly / Change NickServ Password

import twitterservice, db
import socket, ssl
import threading
import json
import time

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#HOST = 'irc.esper.net'
HOST = 'irc.snoonet.org'
PORT = 6697
NICK = 'MaxQ'
admin = 'jclishman'
channels = ['#lishbot]

# Secret credentials :)
credentials = json.load(open('_secret.json'))
password = credentials['nickserv_password']

# Responds to server pings
def pong(text):
    print('PONG' + text.split()[1])
    irc.send(parse('PONG ' + text.split()[1]))

# Makes things human-readable
def parse(string): return bytes(string + '\r\n', 'UTF-8')

# Sends messages
def send_message(message):
	for channel in channels:
		irc.send(parse('PRIVMSG ' + channel + ' :' + message))

# Estabilishes a secure SSL connection
s.connect((HOST, PORT))
irc = ssl.wrap_socket(s)

print('Connecting...')

time.sleep(2)

# Tells the server who it is
irc.send(parse("USER " + NICK + " " + NICK + " " + NICK + " :Bot"))
irc.send(parse("NICK " + NICK))

time.sleep(2)


# Responds to the initial server ping on connection
has_responded_to_ping = False

while not has_responded_to_ping:
    text=irc.recv(1024).decode("UTF-8").strip('\r\n')

    if text.find('PING') != -1:
    	pong(text)
    	has_responded_to_ping = True


time.sleep(2)

# Identifies nickname
irc.send(parse('PRIVMSG NickServ IDENTIFY %s %s' % (NICK, password)))

# Joins channel(s)
for channel in channels:

	irc.send(('JOIN {}\n').format(channel).encode())
	time.sleep(2)

# Threading magic
# I barely understand how this works, so not gonna touch it
class myThread(threading.Thread):
	def __init__(self, threadID, name):
		threading.Thread.__init__(self)
		self.threadID = threadID
		self.name = name

	def run(self):
		print ("Starting " + self.name)
		twitterservice.run()
		print ("Exiting " + self.name)


thread1 = myThread(1, "Twitter thread")
thread1.start()

# Reads messages
# setBlocking needs to be False to allow for the passive sending of messages
irc.setblocking(False)
while True:
	irc_stream = None

	try:
		irc_stream = irc.recv(1024).decode('UTF-8')

	except OSError as e:
		#print("No data")
		time.sleep(0.05)

	if irc_stream is not None: print(irc_stream)

	# Sends ping
	if irc_stream is not None and irc_stream.find('PING') != -1:
		pong(text)
	
	#print(time.ctime())
	if irc_stream is not None and irc_stream.find('PRIVMSG') != -1:

		message_author = irc_stream.split('!',1)[0][1:]
		message_channel = irc_stream.split('PRIVMSG',1)[1].split(':', 1)[0].lstrip()
		message_contents = irc_stream.split('PRIVMSG',1)[1].split(':',1)[1]

		Debugging
		print('Author: ' + message_author)
		print('Channel: ' + message_channel)
		print('Contents: ' + message_contents)

		# Admins can make the bot quit
		if message_author == admin and message_contents.rstrip() == 'bye':
			irc.send(parse("QUIT"))
			print('Exiting...')
			time.sleep(1)
			break 

	start_time = time.time()
	for row in db.get_post_queue():

		# Assembles and sends the IRC message
		send_message('[%s] @%s wrote: %s %s' % (row[1], row[2], row[3], row[4]))
		
		# Sends how long it took from tweet creation to irc message (debug)
		send_message('Took ' + str(round(time.time() - start_time, 5)) + 's')
		#print(str(round(time.time() - start_time, 5)), file=open("output.txt", "a"))
		
		# Anti-bot spam
		time.sleep(1)
		
		# Updates the database after it posts something
		db.update_after_publish(row[0])


irc.close()
