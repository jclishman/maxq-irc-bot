from instagram_web_api import Client, ClientCompatPatch, ClientError, ClientLoginError
from bot_logging import logger
import json
import time
import db

def run():

    web_api = Client(auto_patch=True, drop_incompat_keys=False)

    feed = []
    startup = True
    user_dict = {
        "SpaceX": "20311520", 
        "elonmusk": "17644112", 
        "jclishman.testing": "7400533474"
    }

    while True:
    	for id_str in list(user_dict.values()):
    		try:
    			feed.append(web_api.user_feed(id_str, count=1))
    			time.sleep(1)
    		except Exception as e:
    			logger.error(str(e))
    			logger.error("Error retreiving feed")

    	for post in feed:
    		post = post[0]["node"]

    		user_id_str = post["owner"]["id"]
    		shortcode = post["shortcode"]
    		timestamp = post["created_time"]

    		# Empty string if there isn't a caption
    		try:
    			caption = post["caption"]["text"]
    		except:
    			caption = ''

    		# Match ID number to screenname
    		for screen_name, id_str in user_dict.items():
    			if user_id_str == id_str:
    				user_screen_name = screen_name

    		stored_timestamp = db.get_instagram_timestamp(user_screen_name)

    		if int(timestamp) > stored_timestamp:
    			start_time = time.time()
    			db.update_instagram_timestamp(user_screen_name, int(timestamp))

    			logger.info("New Instagram post by @%s, id %s" % (user_screen_name, user_id_str))
    			logger.info("Post shortcode: %s" % shortcode)
    			logger.info("Post caption: %s" % caption)
    			logger.info("Post timestamp: %s" % timestamp)

    			url = 'https://instagram.com/p/%s' % shortcode
    			if not startup:
    				db.insert_message('Instagram', user_screen_name, caption, url, start_time)
    	
    	time.sleep(10)
    	startup = False