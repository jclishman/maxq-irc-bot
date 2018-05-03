from bot_logging import logger
import requests
import urllib
import urllib.parse
import hashlib
import time
import json
import db
import re

credentials = json.load(open('_config.json'))


def run():
    # Bot won't post anything new on startup
    startup = True

    class InstagramUser:

        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36'
        rhx_gis = None
        csrf_token_cookie = None
        session = requests.Session()

        def __init__(self):

            res = self.session.get('https://instagram.com', headers={'User-Agent': self.user_agent})

            regex_match = re.search(r'"rhx_gis":"(?P<rhx_gis>[a-f0-9]{32})"', res.text)

            if regex_match:
                self.rhx_gis = regex_match.group('rhx_gis')

        def build_signature(self, query_variables):

            m = hashlib.md5()
            m.update('{rhx_gis}:{variables}'.format(rhx_gis=self.rhx_gis, variables=query_variables).encode('utf-8'))
            return m.hexdigest()

        def request(self, **kwargs):

            endpoint_url = None
            signature_var = None
            query_params = kwargs.pop('query_params', {})

            if kwargs['endpoint'] is "username":

                endpoint_url = 'https://instagram.com/' + kwargs['username'] + '/'
                signature_var = urllib.parse.urlparse(endpoint_url).path
                query_params = {'__a': '1'}

            elif kwargs['endpoint'] is "graphql":

                endpoint_url = 'https://instagram.com/graphql/query'
                query_params['query_hash'] = '42323d64886122307be10013ad2dcc44'

                signature_var = query_params['variables'] = json.dumps(kwargs['query_variable'])

            return self.session.get(endpoint_url + "?{}".format(urllib.parse.urlencode(query_params)), headers={
                'User-Agent': self.user_agent, 
                'X-Instagram-GIS': self.build_signature(signature_var)
            })


        def get_user_id(self, username):

            response = self.request(username=username, endpoint='username')

            if response.status_code is not 200:
                logger.error("Instagram responded with status code %s" % str(response.status_code))
                raise Exception("Instagram responded with status_code %s" % str(response.status_code))

            json_response = response.json()

            return json_response['graphql']['user']['id']

        def get_recent_post(self, user_id, **kwargs):

            variables = {
                "id": user_id,
                "first": 1
            }

            response = self.request(endpoint='graphql', query_variable=variables)

            if response.status_code is not 200:
                logger.error("Instagram responded with status code %s" % str(response.status_code))
                raise Exception("Instagram responded with status_code %s" % str(response.status_code))

            post = response.json()['data']['user']['edge_owner_to_timeline_media']['edges'][0]

            post_data = {
                'shortcode': post['node']['shortcode'],
                'created_at_timestamp': post['node']['taken_at_timestamp'],
                'caption': None,
            }

            if len(post['node']['edge_media_to_caption']['edges']) != 0:

                post_data["caption"] = post['node']['edge_media_to_caption']['edges'][0]["node"]["text"]

            return post_data


    users_list = db.get_following('instagram')

    username_list = {x[0] for x in users_list}

    username = ''

    while True:

        for username in username_list:

            # Gets the ID of the post again, and compares it against the stored value
            user = InstagramUser()

            user_id = user.get_user_id(username)
            post_data = user.get_recent_post(user_id)

            stored_timestamp = db.get_instagram_timestamp(username)

            # Is it a new post?
            if post_data["created_at_timestamp"] > stored_timestamp:
                start_time = time.time()

                logger.info('Found new Instagram post')
                logger.info('Shortcode: ' + post_data["shortcode"])
                logger.info('Caption: ' + post_data["caption"])
                logger.info('Timestamp: ' + str(post_data["created_at_timestamp"]))

                db.update_instagram_timestamp(username, post_data["created_at_timestamp"])
                logger.info('Updated database\n')

                if not startup: 
                    db.insert_message('Instagram', username, post_data["caption"], 'https://instagram.com/p/%s' % post_data["shortcode"], start_time)

            else:
                logger.debug('Did not find new post\n')

            time.sleep(3)

        startup = False
