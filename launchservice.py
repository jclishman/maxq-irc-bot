import sys
import socket
import string
import json
import urllib.request
import urllib.parse
from datetime import datetime
from datetime import timedelta
import dateutil.parser

def format_launch(launch_item):
    # prints an item from the LL launches list

    message_parts = [] # list with all the "parts" of the message, name, stream url etc.
    message_parts.append(launch_item["name"])  # name of the launch
    pads = launch_item["location"]["pads"]
    if len(pads) <= 1:
        # add pad name
        message_parts.append(pads[0]["name"])

    if len(launch_item["vidURLs"]) >= 1:
        message_parts.append(launch_item["vidURLs"][0])  # first stream url if available

    net_time = launch_item["net"]  # NET date

    # TBD/NET if unsure otherwise use NET
    net_time = "TBD/NET " + net_time if launch_item["tbdtime"] else "NET " + net_time
    message_parts.append(net_time)

    if not launch_item["tbdtime"]:  # add countdown if it isn't TBD
        launch_time = dateutil.parser.parse(launch_item["isonet"]).replace(tzinfo=None)  # parse launch time
        time_now = datetime.utcnow()

        def format_timedelta(td):
            if td < timedelta(0):
                return '-' + format_timedelta(-td)
            else:
                # Change this to format positive timedeltas the way you want
                return str(td)

        tdelta = format_timedelta(launch_time - time_now)  # Time difference

        # convert to string
        t_minus = "T-" + str(tdelta)[:str(tdelta).index(".")]
        t_minus = t_minus.replace("--", "+")  # two minuses = plus, right?
        message_parts.append(t_minus)

    # return formatted string
    return " - ".join(message_parts)


def get_launch(search):
    # Get launch string from name/search

    search = search.lstrip().rstrip()

    if search.replace(" ", "") == "":
        # no search
        try:
            with urllib.request.urlopen("https://launchlibrary.net/1.4/launch?mode=verbose&next=1") as url:
                data = json.loads(url.read().decode())
                launch_list = data["launches"]
                if len(launch_list) > 0:
                    return format_launch(launch_list[0])
        except urllib.error.HTTPError as e:
            print(str(e))
            return "Useless error message. LL is probably down."

    # Query for search
    time_now = datetime.utcnow()
    url_starttime = time_now.strftime("%Y-%m-%d")
    query = "mode=verbose&limit=1&next=1&name={}"\
            .format(urllib.parse.quote(search))

    # Get the launches
    try:
        with urllib.request.urlopen("https://launchlibrary.net/1.4/launch?" + query) as url:
            data = json.loads(url.read().decode())
            launch_list = data["launches"]

        if len(launch_list) > 0:
            return format_launch(launch_list[0])
        else:
            return f"Next launch for query '{search}' not found."

    except urllib.error.HTTPError:
        return f"Next launch for query '{search}' not found."

