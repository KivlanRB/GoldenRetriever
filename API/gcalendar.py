from __future__ import print_function
import datetime
import os
import pytz
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials


class GoogleAPI():
    def __init__(self) -> None:
        self.scopes = ['https://www.googleapis.com/auth/calendar.readonly']
        self.token = 'token.json'
        self.client_secret = "client_secret.json"
        self.now= datetime.datetime.utcnow().isoformat() + 'Z'
        self.timezone =pytz.timezone("Asia/Jakarta")

    def login(self):
        if not os.path.exists(self.client_secret):
            if not os.path.exists(os.path.join(os.getcwd(), "API", "client_secret.json")):
                raise FileNotFoundError("No client secret detected!")
            else:
                self.client_secret = os.path.join(os.getcwd(), "API", "client_secret.json")
                self.token = os.path.join(os.getcwd(), "API", "token.json")

        creds = None
        if os.path.exists(self.token):
            creds=Credentials.from_authorized_user_file(self.token, self.scopes)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                self.flow = InstalledAppFlow.from_client_secrets_file(self.client_secret, self.scopes)
                creds= self.flow.run_local_server(port=0)
            with open(self.token, 'w') as token:
                token.write(creds.to_json())

        self.service = build('calendar', 'v3', credentials=creds)
        

    def GetTask(self,Date:datetime.date=None,limit=10):
        print('Getting the upcoming {} events'.format(limit))
        now = datetime.datetime.utcnow().isoformat() + 'Z'
        events_result = self.service.events().list(calendarId='primary', timeMin=now, maxResults=limit, singleEvents=True,orderBy='startTime').execute()
        events_list = events_result.get('items', [])
        events=list()

        if not events_list:
            print('No upcoming events found.')
        
        for event in events_list:
            date = event['start'].get('dateTime', event['start'].get('date'))
            try:
                date = datetime.datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                date = datetime.datetime.fromisoformat(date)
            try:
                name = event['summary']
            except KeyError:
                name = "No title"
            events.append({'name':name, 'date':date})

        if bool(Date):
            desired_event = lambda x : x['date'].date() == Date
            event_final = list(filter(desired_event,events))
            return event_final
    
        return events

if __name__ == '__main__':        
    google=GoogleAPI()
    google.login()
    print(google.GetTask())