import json

ACRONYM_FILE = "acronyms.json"

def get_expansion(acronym):

    acronym = acronym.lower().lstrip().rstrip()
    
    with open(ACRONYM_FILE, "r") as file:
        acronyms = json.load(file)

    expansion = "Acronym not found"

    if acronym in acronyms:
        acronyms[acronym]["usage"] += 1
        expansion = f"{acronyms[acronym]['acronym_display']}: {acronyms[acronym]['expansion']}"

    with open(ACRONYM_FILE, "w") as file:
        file.write(json.dumps(acronyms, indent=1, sort_keys=True))
    return expansion

def add_expansion(message):
    message = message.lstrip().rstrip()
    acronym, _, expansion = message.partition(" ")

    with open(ACRONYM_FILE, "r") as file:
        acronyms = json.load(file)

    acronyms[acronym.lower()] = {"acronym": acronym.lower(), "acronym_display": acronym, "expansion": expansion, "usage": 0}

    with open(ACRONYM_FILE, "w") as file:
        file.write(json.dumps(acronyms, indent=1, sort_keys=True))
