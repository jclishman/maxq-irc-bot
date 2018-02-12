import socket
import time
import db

irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
HOST = 'irc.snoonet.org'
PORT = 6667 #port
NICK = 'lishbot'
admin = 'jclishman'
channel = ''
channels = ['#groupofthrones, #lishbot']
password = 'hunter2'

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

irc.connect((HOST, PORT))
print('Connecting...')

# Tells the server who it is
irc.send(parse("USER " + NICK + " " + NICK + " " + NICK + " :GOE bot\r\n"))
irc.send(parse("NICK " + NICK + "\r\n"))

has_responded_to_initial_ping = False

# Responds to the initial server ping on connection
while not has_responded_to_initial_ping:
    text=irc.recv(1024).decode("UTF-8").strip('\r\n')

    if text.find('PING') != -1:
    	pong(text)
    	has_responded_to_initial_ping = True


time.sleep(2)

# Identifies nickname
irc.send(parse('PRIVMSG NickServ IDENTIFY ' + password))

# Joins channel(s)

for channel in channels:

	irc.send(('JOIN ' + channel + '\n').encode())
	time.sleep(2)

# Reads messages
while True:
	#post_queue = []

	irc_stream = irc.recv(1024).decode('UTF-8')
	print(irc_stream)

	# Sends ping
	if irc_stream.find('PING') != -1:
		pong(text)
	
	if irc_stream.find('PRIVMSG') != -1:

		message_author = irc_stream.split('!',1)[0][1:]
		message_channel = irc_stream.split('PRIVMSG',1)[1].split(':', 1)[0].lstrip()
		message_contents = irc_stream.split('PRIVMSG',1)[1].split(':',1)[1]

		# Debugging
		print('Author: ' + message_author)
		print('Channel: ' + message_channel)
		print('Contents: ' + message_contents)

		if message_author == admin and message_contents.rstrip() == 'bye':
			irc.send(parse("QUIT"))
			print('Exiting...')
			time.sleep(1)
			exit() 

	for row in db.get_post_queue():
		message = '[{}] @{} wrote: {} {}'.format(row[1], row[2], row[3], row[4])
		print(message)
		send_message(message)
		db.update_after_publish(row[0])

irc.close()
