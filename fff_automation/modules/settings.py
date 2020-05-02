import os
from trello import TrelloClient
import gspread
import requests
import json

if os.environ.get('PORT') in (None, ""):
    # CODE IS RUN LOCALLY
    LOCAL = True
    print("BOT: Code running locally")
else:
    # CODE IS RUN ON SERVER
    set_enviroment()
    LOCAL = False
    print("BOT: Code running on server")

# IMPORTANT NOTICE
# The correct functionality of the labels depends on these variables and on the label_order variable.
# The latter must reflect the order of the labels in the Trello Board
# The first variables (determined by range()) must reflet the order of the lists in the Board.
# If you want to change the order of the lists in the board, make sure to change the order here, as well as in the order
# that the lists are created in the set_trello() def.
TL_INFORMATION, TL_PLANNEDCALLS, TL_DG, TL_WG, TL_IP, TL_PASTCALLS, TL_ARCHIVE, TB_UPCOMING, TB_CLOSED, TB_RESTRICTED, TB_OPEN, TB_AFRICA, TB_ASIA, TB_EUROPE, TB_GLOBAL, TB_NORTHAMERICA, TB_OCEANIA, TB_PAST, TB_SOUTHAMERICA, = range(
    19)
label_order = ['UPCOMING', 'CLOSED', 'RESTRICTED', 'OPEN', 'AFRICA', 'ASIA',
               'EUROPE', 'GLOBAL', 'NORTH AMERICA', 'OCEANIA', 'PAST', 'SOUTH AMERICA']


def get_var(key, parent="", default=""):
    """
    Retrieve configuration variables from the env_variables.json file.
    :variable: String of the name of the variable you are retrieving (see env_variables.json)
    """
    variables = {}
    with open('fff_automation/secrets/env_variables.json') as variables_file:
        variables = json.load(variables_file)
    if parent == "":
        requested = variables.get(str(key))
    else:
        requested = variables[parent][str(key)]
    print("SETTINGS: Requested: ", requested)
    if requested in ("", None, "insert_here", "insert_here_if_available"):
        if default == "":
            return -1
        else:
            return default
    else:
        return requested


def set_var(key, value):
    """
    Set a variable to the env_variables.json file.
    :key: String (all caps) with the dictionary name of the variable (type str)
    :value: the value of the variable (type str)
    """
    with open('fff_automation/secrets/env_variables.json') as variables_file:
        variables = json.load(variables_file)

    if key in variables:
        del variables[key]
    variables[key] = value

    with open('fff_automation/secrets/env_variables.json', 'w') as output_file:
        json.dump(variables, output_file)
    print("SETTINGS: Set variable ", key)


def set_enviroment():
    variables = {}
    variables['TRELLO_KEY'] = os.environ.get('TRELLO_KEY')
    variables['TRELLO_TOKEN'] = os.environ.get('TRELLO_TOKEN')
    variables['BOT_TOKEN'] = os.environ.get('BOT_TOKEN')
    variables['CALENDAR_ID'] = os.environ.get('CALENDAR_ID')
    variables['GDRIVE_EMAIL'] = os.environ.get('GDRIVE_EMAIL')
    variables['SPREADSHEET'] = os.environ.get('SPREADSHEET')
    variables['TRELLO_BOARD_ID'] = os.environ.get('TRELLO_BOARD_ID')

    save = {}
    for key in variables:
        if variables.get(key) in (None, ''):
            if key == 'SPREADSHEET':
                print("SETTINGS: NO DATABASE FOUND - CREATING NEW SPREADSHEET")
            elif key == 'TRELLO_BOARD_ID':
                print("SETTINGS: NO TRELLO BOARD ID FOUND -  CREATING NEW BOARD")
            else:
                print("SETTINGS: {} IS NOT SET AS ENVIROMENT VARIABLE ON YOUR SERVER -> THIS WILL CAUSE AN ERROR FURTHER IN THE CODE\n Please set a condig variable named {} in your server".format(key, key))
        else:
            save[key] = variables.get(key)

    if os.path.isfile('fff_automation/secrets/env_variables.json') and os.path.getsize('fff_automation/secrets/env_variables.json') > 0:
        with open('fff_automation/secrets/env_variables.json', 'r') as json_file:
            existing_vars = json.load(json_file)
        for key in save:
            if key in existing_vars:
                del existing_vars[key]
                existing_vars[key] = save[key]

    if os.environ.get('CLIENT_SECRET') in (None, ''):
        print("SETTINGS: CLIENT SECRET IS NOT SET AS CONFIG VARIABLE IN YOUR SERVER. THIS WILL NOT ALLOW THE PROGRAM TO ACCESS THE DATABASE AND WILL CAUSE AN ERROR")

    with open('fff_automation/secrets/env_variables.json', 'w') as output_file:
        json.dump(variables, output_file)


def set_trello(client, key, token):
    """
    Setup Trello Board if none exists yet.
    This will save the new board/list/labels ids as enviroment variables
    :client: Trello Client, generated through credentials in the trelloc.py module
    :key: Key of the Trello Client used by the user
    :token: Token of the Trello Client initiated by the user
    """
    # CREATE BOARD
    print("SETTINGS: key ", key)
    print("SETTINGS: token ", token)
    try:
        url = "https://api.trello.com/1/boards/"
        querystring = {"name": "TRANSPARENCY BOARD",
                       "key": key, "token": token}
        response = requests.request("POST", url, params=querystring)
        board_id = response.json()["shortUrl"].split("/")[-1].strip()
        print("SETTINGS: Created New Trello Board")
    except:
        print(
            "SETTINGS: Board could not be created. User might have too many Boards already")
    set_var('TRELLO_BOARD_ID', str(board_id))
    # Delete existing lists
    board = client.get_board(board_id=board_id)
    lists = board.all_lists()
    for trello_list in lists:
        trello_list.close()
    print("SETTINGS: Deleted Existing Lists")
    # Delete existing labels
    labels = board.get_labels()
    for label in labels:
        id = label.id
        url = "https://api.trello.com/1/labels/{id}"
        response = requests.request("DELETE", url)
    print("SETTINGS: Deleted Existing Labels")

    # CREATE LISTS
    # Board info list
    lists = {}
    lists[TL_INFORMATION] = board.add_list(
        name="INFORMATION", pos="bottom").id
    # Calls list
    lists[TL_PLANNEDCALLS] = board.add_list(
        name="PLANNED CALLS", pos="bottom").id
    # discussion groups
    lists[TL_DG] = board.add_list(
        name="DISCUSSION GROUPS", pos="bottom").id
    # working groups
    lists[TL_WG] = board.add_list(
        name="WORKING GROUPS", pos="bottom").id
    # projects groups
    lists[TL_IP] = board.add_list(
        name="INTERNATIONAL PROJECTS", pos="bottom").id
    # past calls
    lists[TL_PASTCALLS] = board.add_list(
        name="PAST CALLS", pos="bottom").id
    # archive
    lists[TL_ARCHIVE] = board.add_list(
        name="ARCHIVE", pos="bottom").id
    set_var("lists", lists)
    print("SETTINGS: Created Lists")

    # CREATE LABELS
    labels = {}
    labels[TB_UPCOMING] = board.add_label(
        name="UPCOMING", color="yellow").id
    labels[TB_CLOSED] = board.add_label(
        name="CLOSED GROUP", color="purple").id
    labels[TB_RESTRICTED] = board.add_label(
        name="RESTRICTED GROUP", color="blue").id
    labels[TB_OPEN] = board.add_label(
        name="OPEN GROUP", color="sky").id
    labels[TB_AFRICA] = board.add_label(
        name="AFRICA", color="black").id
    labels[TB_ASIA] = board.add_label(
        name="ASIA", color="black").id
    labels[TB_EUROPE] = board.add_label(
        name="EUROPE", color="black").id
    labels[TB_NORTHAMERICA] = board.add_label(
        name="NORTH AMERICA", color="black").id
    labels[TB_SOUTHAMERICA] = board.add_label(
        name="SOUTH AMERICA", color="black").id
    labels[TB_OCEANIA] = board.add_label(
        name="OCEANIA", color="black").id
    labels[TB_GLOBAL] = board.add_label(
        name="GLOBAL", color="black").id
    labels[TB_PAST] = board.add_label(
        name="PAST CALL", color="black").id
    set_var('labels', labels)
    print("SETTINGS: Created Labels")

    # CREATE INFO CARD
    client.get_list(get_var(TL_INFORMATION, 'lists')).add_card(name="IMPORTANT INFORMATION",
                                                               desc="You can edit the cards in the \"INFORMATION\" list as you wish, but don't edit the cards nor the list order of the other lists as it might break the way the code works.")
    print("SETTINGS: Created Info Card")


def set_database(client):
    """
    Setup spreadsheet database if none exists yet.
    Will save the spreadsheet ID to env_variables.json
    The service email you created throught the Google API will create the new spreadsheet and share it with the email you indicated in the GDRIVE_EMAIL enviroment variable. You will find the spreadsheet database in your google drive shared folder.
    Don't change the order of the worksheets or it will break the code.
    :credentials: Credentials created in database.py
    """
    # CREATE SPREADSHEET
    spreadsheet = client.create('DATABASE')
    set_var('SPREADSHEET', spreadsheet.id)
    print("SETTINGS: Created Spreadsheet")

    # CREATE GROUP CHATS SHEET
    groupchats = spreadsheet.add_worksheet(
        title="Groupchats", rows="150", cols="15")
    groupchats.append_row(["GROUP ID", "CARD ID", "TITLE", "CATEGORY", "REGION", "ADMINS", "PLATFORM",
                           "COLOR", "RESTRICTION", "IS SUBGROUP", "PARENT GROUP", "PURPOSE", "ONBOARDING", "TRELLO CARD", "LINK"])
    print("SETTINGS: Created Groupchats Sheet")

    # CREATE ARCHIVE SHEET
    archive = spreadsheet.add_worksheet(title="Archive", rows="150", cols="13")
    archive.append_row(["GROUP ID", "CARD ID", "TITLE", "CATEGORY", "REGION", "ADMINS",
                        "PLATFORM", "COLOR", "PURPOSE", "ONBOARDING", "TRELLO LINK", "DATE OF ARCHIVAL"])
    print("SETTINGS: Created Archive Sheet")

    # CREATE DELETED SHEET
    deleted = spreadsheet.add_worksheet(title="Deleted", rows="150", cols="11")
    deleted.append_row(["TITLE", "CATEGORY", "REGION", "ADMINS", "PLATFORM", "COLOR",
                        "RESTRICTION", "PURPOSE", "ONBOARDING", "DATE OF DELETION", "DELETED BY"])
    print("SETTINGS: Created Deleted Sheet")

    # DELETE PRE-EXISTING SHEET
    sheet = spreadsheet.get_worksheet(0)
    spreadsheet.del_worksheet(sheet)
    print("SETTINGS: Deleted Pre Existing sheet")

    # SHARE SPREADSHEET
    spreadsheet.share(value=get_var('GDRIVE_EMAIL'),
                      perm_type="user", role="owner")
    print("SETTINGS: Shared Spreadsheet with ", get_var('GDRIVE_EMAIL'))