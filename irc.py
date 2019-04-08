# Reddit AMA mode

from bot_logging import logger
import twitterservice, instagramservice, redditservice, launchservice, acronymservice
import commands, db, wolfram
import socket, ssl
import threading
import time
import math
import json
import os

logger.info("Now Entering MaxQ...")

# Secret credentials :)
config = json.load(open("_config.json"))
password = config["nickserv_password"]

# IRC Config
HOST = "irc.esper.net"
# HOST = "irc.snoonet.org"
PORT = 6697
NICK = "MaxQ"
admins = config["admin_hostnames"]
channels = ["#SpaceX"]


# Responds to server pings
def pong(text):
    logger.debug("PONG" + text.split()[1])
    irc.send(parse("PONG " + text.split()[1]))


# Helper methods
def parse(string): return bytes(string + "\r\n", "UTF-8")


def send_message_to_channels(message):
    for channel in channels:
        send_privmsg(channel, message)


def send_message_to_channel(channel, message):
    send_privmsg(channel, message)


def send_privmsg(target, message):
    irc.send(parse(f"PRIVMSG {target} :{message}"))

def restart_irc():
    logger.info("Restarting...")
    os.system("nohup python3 irc &")
    time.sleep(5)
    irc.send(parse("QUIT :Be right back!"))
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

logger.info("Connecting...")

time.sleep(5)

# Tells the server who it is
irc.send(parse(f"USER {NICK} {NICK} {NICK} :Bot"))
irc.send(parse(f"NICK {NICK}"))
logger.info("Server Ident")

# Responds to the initial server ping on connection
has_responded_to_ping = False

while not has_responded_to_ping:
    text = irc.recv(1024).decode("UTF-8").strip("\r\n")

    if text.find("PING") != -1:
        pong(text)
        has_responded_to_ping = True


# Creates and starts threads
def twitter_thread():
    logger.info("Starting Twitter Thread")
    twitterservice.run()


def insta_thread():
    logger.info("Starting Instragram Thread")
    instagramservice.run()


def reddit_thread():
    logger.info("Starting Reddit Thread")
    redditservice.run()


twitter = threading.Thread(name="Twitter_Thread", target=twitter_thread)
insta = threading.Thread(name="Instagram_Thread", target=insta_thread)
reddit = threading.Thread(name="Reddit_Thread", target=reddit_thread)

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
irc.send(parse(f"NickServ IDENTIFY {NICK} {password}\n"))
logger.info("NickServ Ident")

time.sleep(2)

# Joins channel(s)
for channel in channels:
    irc.send((f"JOIN {channel}\n").encode())
    time.sleep(2)

while True:
    irc_stream = None

    try:
        irc_stream = str(irc.recv(1024), "UTF-8", errors="replace")

    except OSError as e:
        time.sleep(0.01)

    if irc_stream is not None:
        logger.info(irc_stream)

    # Sends server ping
    if irc_stream is not None and irc_stream.find("PING") != -1:
        pong(text)

    # print(time.ctime())
    if irc_stream is not None and irc_stream.find("PRIVMSG") != -1:
        is_privmsg = False

        message_author = irc_stream.split('!', 1)[0][1:]
        message_channel = irc_stream.split("PRIVMSG", 1)[1].split(':', 1)[0].lstrip()
        message_contents = irc_stream.split("PRIVMSG", 1)[1].split(':', 1)[1]

        try:
            message_author_hostname = irc_stream.split('@', 1)[1].split()[0]
        except IndexError as e:
            logger.error(str(e))
            message_author_hostname = ''

        logger.info("Author: " + message_author)
        logger.info("Hostname: " + message_author_hostname)
        logger.info("Channel: " + message_channel)
        logger.info("Content: " + message_contents)

        if not message_channel.startswith('#'): is_privmsg = True

        # Admins can make the bot check status, restart, and quit
        if message_author_hostname in admins or message_author.starts_with('j'):

            if message_contents.rstrip() == ".status":
                status = get_status()

                message = (f"Alive: Twitter - {status[0]} | Instagram - {status[1]} | Reddit - {status[2]}")
                logger.info(message)

                if not is_privmsg: send_message_to_channel(message_channel, message)
                else: send_privmsg(message_author, message)
            
            elif message_contents.rstrip() == ".restart":
                restart_irc()
                os.system("exit")

            elif message_contents.rstrip() == ".quit":
                irc.send(parse("QUIT :HTTP Error 418 - Stuck in orbit between Earth and Mars."))
                logger.info("Exiting")
                exit()

            elif message_contents.rstrip() == ".following":
                twitter_following = {'@' + x[0] for x in db.get_following("twitter")}
                instagram_following = {'@' + x[0] for x in db.get_following("instagram")}

                send_privmsg(message_author, f"Twitter: {twitter_following}")
                send_privmsg(message_author, f"Instagram: {instagram_following}")


            elif ".say" in message_contents.rstrip():
                send_message_to_channels(message_contents.replace(".say ", ''))
            
            elif message_contents.startswith(".add"):
                acronym = message_contents.replace(".add ", '')
                acronymservice.add_expansion(acronym)

                logger.info(f"Added acronym {acronym}")
                send_message_to_channels(f"Added acronym {acronym}")

            elif message_contents.startswith(f"{NICK}: ") and not is_privmsg:
                logger.info("Got command")

                parsed_command = commands.parse(message_contents)
                send_message_to_channel(message_channel, parsed_command)
                logger.info(f"Returned: {parsed_command}")

            elif is_privmsg:
                logger.info("Got command as PM")

                parsed_command = commands.parse(message_contents)
                send_privmsg(message_author, parsed_command)
                logger.info(f"Returned: {parsed_command}")

        if message_contents.rstrip().startswith(".tell"):

            message_clean = message_contents.replace(".tell ", '')
            letter = message_clean.split(' ')
            sender = message_author
            recipient  = letter[0].lower()
            mail_content = ' '.join(letter[1:])

            logger.info("Mail received")
            logger.info(f"Sender: {sender}")
            logger.info(f"Recipient : {recipient }")
            logger.info(f"Mail Content: {mail_content}")

            db.send_mail(sender, recipient , int(time.time()), mail_content)
            send_message_to_channel(message_channel, f"Message sent to {recipient}.")

        
        if message_contents.rstrip().startswith(".wa"):
            
            message_clean = message_contents.replace(".wa ", '')
            send_message_to_channel(message_channel, wolfram.get_wa(message_clean))

            
        if message_contents.rstrip().startswith(".nextlaunch"):
            
            try:
                launch_param = message_contents.rstrip().replace(".nextlaunch", '')
                logger.info("Got launch with parameters " + str(launch_param))

            except:
                logger.info("Got launch with no parameters")
                launch_param = ''

            send_message_to_channel(message_channel, launchservice.get_launch(launch_param)) 

        if message_contents.rstrip().startswith(".expand"):
        
            try:
                expand_param = message_contents.rstrip().replace(".expand ", '')
            except:
                expand_param = ''
            
            logger.info(f"Got expand with parameter {expand_param}")
            expansion = acronymservice.get_expansion(expand_param)
            
            send_message_to_channel(message_channel, expansion)
            
        for row in db.get_mail(message_author.lower()):
            #print("Getting mail")

            time_between = int(time.time() - row[3])
            #print(f"Time between: {time_between}")

            # Days
            if time_between > 86400:
                days = math.floor(time_between / 86400)
                time_between -= (days * 86400)

            else: days = 0

            # Hours
            if time_between > 3600:
                hours = math.floor(time_between / 3600)
                time_between -= (hours * 3600)

            else: hours = 0

            # Minutes
            if time_between > 60:
                minutes = math.floor(time_between / 60)
                time_between -= (minutes * 60)

            else: minutes = 0

            seconds = time_between

            timeDiffStr = f"{days}d {hours}h {minutes}m {seconds}s ago"

            send_message_to_channel(message_channel, f"{message_author}: New message from {row[1]} sent {timeDiffStr}: {row[4]}")
            logger.info(f"Deilvered message for {message_author} (ID: {row[0]})")



    for row in db.get_post_queue():

        # Assembles and sends the IRC message
        # Platform-specific formatting
        if row[1] == "Instagram" or row[1] == "Twitter":

            msg = f"[{row[1]}] @{row[2]} wrote: {row[3]} {row[4]}"

            send_message_to_channels(msg)
            logger.info(msg)

        elif row[1] == "Reddit":

            msg = f"[{row[1]}] {row[2]} {row[3]}"

            send_message_to_channels(msg)
            logger.info(msg)


        # Sends how long it took from tweet creation to irc message (debug)
        time_to_post = round(time.time() - row[6], 5)
        logger.info(f"Post #{row[0]}, Took {time_to_post}s\n")

        # Updates the database after it posts something
        db.update_after_publish(row[0])

