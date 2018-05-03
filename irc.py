# Reddit AMA mode

from bot_logging import logger
import twitterservice, instagramservice, redditservice
import commands, db
import socket, ssl
import threading
import time
import json
import os

logger.info('Now Entering MaxQ...')

# Secret credentials :)
config = json.load(open('_config.json'))
password = config['nickserv_password']

# IRC Config
# HOST = 'irc.esper.net'
HOST = 'irc.snoonet.org'
PORT = 6697
NICK = 'MaxQ'
admins = config["admin_hostnames"]
channels = ['#groupofthrones']


# Responds to server pings
def pong(text):
    logger.debug('PONG' + text.split()[1])
    irc.send(parse('PONG ' + text.split()[1]))


# Helper methods
def parse(string): return bytes(string + '\r\n', 'UTF-8')


def send_message_to_channels(message):
    for channel in channels:
        send_privmsg(channel, message)


def send_message_to_channel(channel, message):
    send_privmsg(channel, message)


def send_privmsg(target, message):
    irc.send(parse('PRIVMSG  %s :%s' % (target, message)))


def restart_irc():
    logger.info('Restarting...')
    os.system('start cmd /c irc.py')
    time.sleep(5)
    irc.send(parse('QUIT :Be right back!'))
    exit()


def get_status():
    twitter_alive = twitter.is_alive()
    insta_alive = insta.is_alive()
    reddit_alive = reddit.is_alive()

    return [twitter_alive, insta_alive, reddit_alive]

# Establishes a secure SSL connection
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))
irc = ssl.wrap_socket(s)

logger.info('Connecting...')

time.sleep(5)

# Tells the server who it is
irc.send(parse('USER ' + NICK + ' ' + NICK + ' ' + NICK + ' :Bot'))
irc.send(parse('NICK ' + NICK))
logger.info('Server Ident')

# Responds to the initial server ping on connection
has_responded_to_ping = False

while not has_responded_to_ping:
    text = irc.recv(1024).decode('UTF-8').strip('\r\n')

    if text.find('PING') != -1:
        pong(text)
        has_responded_to_ping = True


# Creates and starts threads
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

# Set to true so that threads exit on IRC quit
twitter.daemon = True
insta.daemon = True
reddit.daemon = True

# Finally, start all the threads
twitter.start()
insta.start()
reddit.start()

# Reads messages
# setBlocking needs to be False to allow for the passive sending of messages
irc.setblocking(False)

time.sleep(2)

# Identifies nickname
irc.send(parse(('NickServ IDENTIFY %s %s\n' % (NICK, password))))
logger.info('NickServ Ident')

# Joins channel(s)
for channel in channels:
    irc.send(('JOIN %s\n' % channel).encode())
    time.sleep(2)

while True:
    irc_stream = None

    try:
        irc_stream = str(irc.recv(1024), 'UTF-8', errors='replace')

    except OSError as e:
        time.sleep(0.01)

    if irc_stream is not None:
        logger.info(irc_stream)

    # Sends server ping
    if irc_stream is not None and irc_stream.find('PING') != -1:
        pong(text)

    # print(time.ctime())
    if irc_stream is not None and irc_stream.find('PRIVMSG') != -1:
        is_privmsg = False

        message_author = irc_stream.split('!', 1)[0][1:]
        message_channel = irc_stream.split('PRIVMSG', 1)[1].split(':', 1)[0].lstrip()
        message_contents = irc_stream.split('PRIVMSG', 1)[1].split(':', 1)[1]

        try:
            message_author_hostname = irc_stream.split('@', 1)[1].split()[0]
        except IndexError as e:
            logger.error(str(e))
            message_author_hostname = ''

        logger.info('Author: ' + message_author)
        logger.info('Hostname: ' + message_author_hostname)
        logger.info('Channel: ' + message_channel)
        logger.info('Content: ' + message_contents)

        if not message_channel.startswith('#'): is_privmsg = True

        # Admins can make the bot check status, restart, and quit
        if message_author_hostname in admins:

            if message_contents.rstrip() == '!!status':
                status = get_status()

                message = 'Alive: Twitter - %r | Instagram - %r | Reddit - %r' % (status[0], status[1], status[2])
                logger.info(message)

                if not is_privmsg: send_message_to_channel(message_channel, message)
                else: send_privmsg(message_author, message)

            elif message_contents.rstrip() == '!!restart':
                restart_irc()
                os.system('exit')

            elif message_contents.rstrip() == '!!quit':
                irc.send(parse('QUIT :HTTP Error 418 - Stuck in orbit between Earth and Mars.'))
                logger.info('Exiting')
                exit()

            elif message_contents.rstrip() == '!!following':
                twitter_following = {'@' + x[0] for x in db.get_following('twitter')}
                instagram_following = {'@' + x[0] for x in db.get_following('instagram')}

                send_privmsg(message_author, 'Twitter: ' + str(twitter_following))
                send_privmsg(message_author, 'Instagram: ' + str(instagram_following))

            elif message_contents.startswith(("%s: ") % NICK) and not is_privmsg:
                logger.info('Got command')

                parsed_command = commands.parse(message_contents)
                send_message_to_channel(message_channel, parsed_command)
                logger.info('Returned: ' + parsed_command)

            elif is_privmsg:
                logger.info('Got command as PM')

                parsed_command = commands.parse(message_contents)
                send_privmsg(message_author, parsed_command)
                logger.info('Returned: ' + parsed_command)

    for row in db.get_post_queue():

        # Assembles and sends the IRC message
        # Platform-specific formatting
        if row[1] == 'Instagram' or row[1] == 'Twitter':
            send_message_to_channels('[%s] @%s wrote: %s %s' % (row[1], row[2], row[3].replace('\n', ' '), row[4]))
            logger.info('[%s] @%s wrote: %s %s' % (row[1], row[2], row[3].replace('\n', ' '), row[4]))

        elif row[1] == 'Reddit':
            send_message_to_channels('[%s] %s %s' % (row[1], row[3], row[4]))
            logger.info('[%s] %s %s' % (row[1], row[3], row[4]))

        # Sends how long it took from tweet creation to irc message (debug)
        logger.info('Post #' + str(row[0]) + ', Took ' + str(round(time.time() - row[6], 5)) + 's\n')

        # Updates the database after it posts something
        db.update_after_publish(row[0])

