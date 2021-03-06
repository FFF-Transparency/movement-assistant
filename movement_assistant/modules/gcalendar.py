from __future__ import print_function
import datetime
import pickle
import os
import json
from datetime import datetime, timedelta
from movement_assistant.modules import utils, settings, database
from movement_assistant.classes.botupdate import BotUpdate
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials
from google.auth.transport.requests import Request

LAVENDER, SAGE, GRAPE, FLAMINGO, BANANA, TANGERINE, PEACOCK, GRAPHITE, BLUEBERRY, BASIL = range(1, 11)
colors = {
    LAVENDER: 'Lavender',
    SAGE: 'Sage',
    GRAPE: 'Grape',
    FLAMINGO: 'Flamingo',
    BANANA: 'Banana',
    TANGERINE: 'Tangerine',
    PEACOCK: 'Peacock',
    GRAPHITE: 'Graphite',
    BLUEBERRY: 'Blueberry',
    BASIL: 'Basil'
}

if not (os.path.isfile('movement_assistant/secrets/calendar_token.pkl') and os.path.getsize('movement_assistant/secrets/calendar_token.pkl') > 0):
    scope = ['https://www.googleapis.com/auth/calendar', 'https://www.googleapis.com/auth/calendar.events']
    # CREDENTIALS HAVE NOT BEEN INITIALIZED BEFORE
    client_secret = os.environ.get('CLIENT_SECRET')
    if client_secret != None:
        # CODE RUNNING ON SERVER
        client_secret_dict = json.loads(client_secret)
        print("JSON CLIENT SECRET:  ", type(client_secret_dict))
    else:
        # CODE RUNNING LOCALLY
        print("CALENDAR: Resorted to local JSON file")
        with open('movement_assistant/secrets/client_secret.json') as json_file:
            client_secret_dict = json.load(json_file)

    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        client_secret_dict, scopes=scope)
    pickle.dump(creds, open(
        "movement_assistant/secrets/calendar_token.pkl", "wb"))


credentials = pickle.load(
    open("movement_assistant/secrets/calendar_token.pkl", "rb"))
service = build('calendar', 'v3', credentials=credentials)


def add_event(botupdate, date, time, duration, title, description, group, color):
    print("CALENDAR: Time type: ", type(time), ' ', time)
    print("CALENDAR: Date type: ", type(date), ' ', date)

    start_date = datetime.combine(date, time)
    print("CALENDAR: Start time string: ", start_date)
    print(type(start_date))
    # Get end time calculating with the duration
    print("CALENDAR: Duration string: ", duration)
    duration = timedelta(seconds=int(duration))
    print("CALENDAR: Duration: " + str(duration))
    print("CALENDAR: type: ", type(duration))

    end_time = start_date + duration
    print("CALENDAR: End time: " + str(end_time))
    print(type(end_time))

    GMT_OFF = '+00:00'
    event = {
        'summary': title,
        'location': group,
        'start': {
            'dateTime': start_date.strftime("%Y-%m-%dT%H:%M:%S"),
            'timeZone': GMT_OFF,
        },
        'end': {
            'dateTime': end_time.strftime("%Y-%m-%dT%H:%M:%S"),
            'timeZone': GMT_OFF,
        },
        'description': utils.format_call_info(botupdate, platform='Calendar'),
        'colorId': str(color),
    }

    calendar_id = settings.get_var(key='CALENDAR_ID', default='primary')
    saved_event = service.events().insert(calendarId=calendar_id, body=event,
                                          sendNotifications=True).execute()
    url = saved_event.get('htmlLink')
    event_id = saved_event['id']
    return [event_id, url]


def edit_event(botupdate, gbotupdate=None):
    calendar_id = settings.get_var(key='CALENDAR_ID', default='primary')
    #try:

    start_date = datetime.combine(botupdate.obj.date, botupdate.obj.time)
    print("CALENDAR: Start time string: ", start_date)
    print(type(start_date))
    # Get end time calculating with the duration
    print("CALENDAR: Duration string: ", botupdate.obj.duration)
    duration = timedelta(seconds=int(botupdate.obj.duration))
    print("CALENDAR: Duration: " + str(duration))
    print("CALENDAR: type: ", type(duration))

    end_time = start_date + duration
    print("CALENDAR: End time: " + str(end_time))
    print(type(end_time))

    event = service.events().get(calendarId=calendar_id, eventId=botupdate.obj.id).execute()
    event['summary'] = botupdate.obj.title
    event['start']['dateTime'] = start_date.strftime("%Y-%m-%dT%H:%M:%S")
    event['end']['dateTime'] = end_time.strftime("%Y-%m-%dT%H:%M:%S")
    event['description'] = utils.format_call_info(botupdate, platform='Calendar')
    color = gbotupdate.obj.color if gbotupdate else database.get(botupdate.obj.chat_id)[0].color
    event['colorId'] = color

    service.events().update(calendarId=calendar_id, eventId=event['id'], body=event).execute()


def delete_event(event_id):
    calendar_id = settings.get_var(key='CALENDAR_ID', default='primary')
    print("CALENDAR: Delete Event: Id: ", event_id)
    try:
        service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
    except:
        print('GCALENDAR: Error in Deleting Call Event')


def clear_data():
    calendar_id = settings.get_var(key='CALENDAR_ID', default='primary')
    page_token = None
    while True:
        events = service.events().list(calendarId=calendar_id, pageToken=page_token).execute()
        for event in events['items']:
            delete_event(event['id'])
        page_token = events.get('nextPageToken')
        if not page_token:
            break