import logging
import os
import os.path

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

TABLE_RANGE = 'transaction_db!A:F'

load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s, %(levelname)s, %(message)s',
    filename='main.log',
    filemode='a',
)


def get_sheet():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json',
                SCOPES,
            )
            creds = flow.run_local_server(port=0)

        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    sheet = build('sheets', 'v4', credentials=creds).spreadsheets()
    return sheet


def get_values():
    sheet = get_sheet()
    try:
        result = (
            sheet.values()
            .get(spreadsheetId=os.getenv('SHEET_ID'), range=TABLE_RANGE)
            .execute()
        )
        values = result.get('values', [])

        if not values:
            print('No data found.')
            return
        return values

    except HttpError as err:
        print(err)


def get_last_values(count=5):
    data = get_values()
    return data[-count:]


def append_values(transaction_data):
    sheet = get_sheet()
    body = {
        'range': TABLE_RANGE,
        'values': [transaction_data],
    }
    try:
        sheet.values().append(
            spreadsheetId=os.getenv('SHEET_ID'),
            range=TABLE_RANGE,
            body=body,
            valueInputOption='RAW',
        ).execute()
    except HttpError as err:
        logging.critical(err)
