import sys
import socket
import string
import json
import requests
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

    search = search.lstrip().rstrip().lower()

    # common launch providers and aliases
    aliases = {
        "boeing":"ba",
        "lockheed martin":"lmt",
        "arianespace": "asa",
        "spacex":"spx",
        "roscosmos": "rfsa"
    }

    LSPs = ["isro", "jaxa", "nasa", "cnes", "ba", "lmt", "casic", "asa", "ils", "spx", "ula", "rfsa"]
    
    # alias the names
    search = aliases[search] if search in aliases else search

    # search using launch provider name if valid
    search_type = "lsp" if search in LSPs else "name"

    # increments for more launches in the future (.nextlaunch +1 etc.)
    launchnum = 1
    if len(search) > 0 and search[0] == "+":
        try:
            launchnum = 1 + int(search)
        except ValueError:
            return(f"Invalid integer")

        if launchnum > 5 or launchnum < 0:
            return(f"Integer out of range")

        # empty search string get next launches
        search = ""

    try:
        response = requests.get(
            url="https://launchlibrary.net/1.4.1/launch",
            params={
                "mode": "verbose",
                "next": launchnum,
                "limit": launchnum,
                search_type: search
                },
            headers={
                "User-Agent": "MaxQ IRC Bot; linux; compatible;",
                "Accept": "*/*"
            })

    except requests.exceptions.RequestException:
        return(f'HTTP Error {response.status_code}, LaunchLibrary might be down.')

    if response.status_code == 404:
        return(f"Nothing found for query '{search}'. Try something else!")

    data = response.json()
    launch_list = data["launches"]

    if len(launch_list) > 0:
        # last item in list
        return format_launch(launch_list[-1])

    time_now = datetime.utcnow()
    url_starttime = time_now.strftime("%Y-%m-%d")
    