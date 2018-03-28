import requests
import urllib
import urllib.parse
import json
import db

users_list = db.get_following("instagram")

print (users_list)

following = {x[1] for x in users_list}

print (following)