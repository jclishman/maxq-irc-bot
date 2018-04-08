from bot_logging import logger
import requests
import urllib
import urllib.parse
import time
import json
import db


def get_instagram_data(username):
    return requests.get(('https://www.instagram.com/%s/?__a=1') % username)


def run():
    # Bot won't post anything new on startup
    startup = True

    class InstagramUser():
        name = ''
        info = ''
        post_id = ''
        post_timestamp = ''
        post_caption = ''

        def get_data(self):

            try:
                self.json = json.loads(self.info.text)

            except Exception as e:
                status_code = str(self.info.status_code)

                # Error handling
                logger.error('Status Code: ' + status_code)
                logger.error(str(e))
                logger.error('Waiting for 2 minutes, then trying again')
                time.sleep(120)

                self.json = json.loads(self.info.text)

            # JSON for the most recent post id
            self.post_id = self.json['graphql']['user']['edge_owner_to_timeline_media']['edges'][0]['node']['shortcode']

            # JSON for the most recent post timestamp
            self.post_timestamp = self.json['graphql']['user']['edge_owner_to_timeline_media']['edges'][0]['node'][
                'taken_at_timestamp']

    users_list = db.get_following('instagram')

    username_list = {x[0] for x in users_list}

    username = ''
    UserObjectList = []

    while True:

        for username in username_list:

            # Gets the ID of the post again, and compares it against the stored value
            user = InstagramUser()

            user.name = username
            stored_timestamp = db.get_instagram_timestamp(user.name)
            user.info = get_instagram_data(user.name)

            user.get_data()

            logger.debug('Status Code: ' + str(user.info.status_code))
            logger.debug('Name: ' + str(user.name))
            logger.debug('New timestamp: ' + str(user.post_timestamp))
            logger.debug('Previous timestamp: ' + str(stored_timestamp))

            # Rate limiter
            time.sleep(3.5)

            # Is it a new post?
            if user.post_timestamp > stored_timestamp:
                start_time = time.time()

                # Tries to get the post caption, if there is one
                try:
                    user.post_caption = user.json['graphql']['user']['edge_owner_to_timeline_media']['edges'][0]['node']['edge_media_to_caption']['edges'][0]['node']['text']
                    
                except IndexError:
                    user.post_caption = ''

                logger.info('Found new Instagram post')
                logger.debug('Shortcode: ' + user.post_id)
                logger.debug('Caption: ' + user.post_caption)
                logger.debug('Timestamp: ' + str(user.post_timestamp))

                db.update_instagram_timestamp(user.name, str(user.post_timestamp))
                logger.info('Updated database\n')

                if not startup: db.insert_message('Instagram', user.name, user.post_caption, 'https://instagram.com/p/%s' % user.post_id, start_time)

            else:
                logger.debug('Did not find new post\n')

        startup = False
