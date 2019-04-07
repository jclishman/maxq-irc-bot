from bot_logging import logger
import twitterservice as twitter
import time
import db

NICK = 'MaxQ'

def parse(message_contents):
    # Default values
    retweets = 0
    replies = 0

    # Makes everything lowercase, removes the bot username, and take out all spaces
    message_clean = message_contents.replace(NICK + ': ', '').lower()

    # Splits the command into parts
    command = message_clean.split(' ')
    action = command[0].strip()

    # Error handling
    try: target = command[1].replace('@', '').strip()
    except: target = None

    try: retweets = int(command[2].strip())
    except: retweets = None

    try: replies = int(command[3].strip())
    except: replies = None

    if action == 'help':

        if target == 'follow': return 'Follows Twitter accounts, see MaxQ: help for syntax'
        elif target == 'unfollow': return 'Unfollows Twitter accounts, see MaxQ: help for syntax'
        elif target == 'set': return 'Changes flag(s) for accounts I\'m already following, see MaxQ: help for syntax'
        else: return 'Syntax: MaxQ: follow|unfollow|set @username 0|1 <retweets> 0|1 <replies>'

    elif action == 'unfollow':

        user_id = twitter.getID(target)

        if in_database(user_id):
            db.unfollow_account(user_id)
            return 'Unfollowed @%s' % target

        elif not in_database(user_id):
            return 'Error: @%s is not in the database' % target

    if type(retweets) is not int or type(replies) is not int:
        logger.error('Command error: not an int')
        return 'Error: Invalid command'

    if retweets > 1 or replies > 1:
        logger.error('Command Error: not 0 or 1')
        return 'Error: Invalid command'

    # print('Command: ' + str(command))
    logger.info(f"Action: {action} | Target: {target} | Retweets: {retweets} | Replies: {replies}")

    if target is not None:

        user_id = twitter.getID(target)

        # Is the target a user? Does the user actually exist?
        if user_id is not None:

            # Are flags specified?
            if retweets is not None and replies is not None:

                if action == 'follow':

                    # Is the user not already in the database?
                    if not in_database(user_id):
                        db.follow_account(target, user_id, retweets, replies)
                        return f"@{target} is now being followed on Twitter | Retweets {retweets} | Replies {replies}"

                    elif in_database(user_id):
                        return f"@{target} is already being followed on Twitter"

                if action == 'set':

                    if in_database(user_id):
                        db.set_flags(user_id, retweets, replies)
                        return f"@{target} now has retweets set to {retweets} and replies set to {replies}"

                    elif not in_database(user_id):
                        return f"Error: @{target} is not in the database"

            else: return 'Error: Missing valid flag(s)'

        elif user_id is None: return f"Error: @{target} does not exist"

    else: return 'Error: No target account'

def in_database(user_id):
    users_list = db.get_following('twitter')
    for row in users_list:
        if str(user_id) in row[1]: return True
