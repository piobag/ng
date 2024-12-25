from os import getenv, path
import pickle
import pytz

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from pymongo import MongoClient
import gridfs

tz = pytz.timezone('America/Sao_Paulo')

APP = 'calendar'
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/calendar.settings.readonly'
]

TOKEN_PATH = f'{APP}.token'
CREDENTIALS = "credentials.json"

# MongoDB
db = MongoClient(getenv('MONGO_URI')).get_database()
fs = gridfs.GridFS(db)
col = db['google']
doc = col.find_one({'app': APP})
if not doc:
    print('\ngerando collection\n')
    col.insert_one({'app': APP})
    doc = col.find_one({'app': APP})

def init_google(app, scopes):
    # Get token from GridFS
    token = fs.find_one({'app': app, 'filename': TOKEN_PATH})
    if token:
        with open(TOKEN_PATH, 'wb') as tokenfile:
            tokenfile.write(token.read())
    else:
        print('\nToken not found in gridfs.\n')
    # Create google service
    creds = None
    if path.isfile(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, scopes)
        # with open(TOKEN_PATH, 'rb') as token:
        #     creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS, scopes)
            # creds = flow.run_local_server(port=0)
            creds = flow.run_console()
        # with open(TOKEN_PATH, 'wb') as tokenfile:
        #     pickle.dump(creds, tokenfile) # tokenfile.write(creds.to_dict())
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_dict())
        with open(TOKEN_PATH, 'rb') as tokenfile:
            id = fs.put(tokenfile.read(), app=app, filename=TOKEN_PATH)
    service = build(app, 'v3', credentials=creds)
    return service


def create_event(event):
    service = init_google(APP, SCOPES)
    print('Getting the upcoming 10 events')
    from datetime import datetime
    now = datetime.now(tz)
    events_result = service.events().list(calendarId='primary', timeMin=now,
                                        maxResults=10, singleEvents=True,
                                        orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        print('No upcoming events found.')
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        print(start, event['summary'])


# from os import getenv, path, mkdir
# from io import FileIO
# from datetime import datetime

# from googleapiclient.discovery import build
# from google_auth_oauthlib.flow import InstalledAppFlow
# from google.auth.transport.requests import Request
#  # from google.oauth2.credentials import Credentials
# from googleapiclient.http import MediaIoBaseDownload
# from mail import send_mail


# # Verificar se tem pendentes

# # Dump modified files from Drive
# def dump_drive(drive):
#     files = doc.get('pending_files')
#     if files:
#         print(f'{len(files)} pending files to download found...')
#     else:
#         print('Searching online for new files...')
#         files = []
#         page_token = None
#         query = f"modifiedTime > '{doc['last_sync'].strftime('%Y-%m-%dT%H:%M:%S')}'"
#         query_time = datetime.utcnow()
#         while True:
#             response = drive.files().list(
#                 q=query,
#                 pageSize=50,
#                 spaces='drive',
#                 fields='nextPageToken, files(id, name, parents, mimeType, modifiedTime, createdTime)',
#                 pageToken=page_token
#             ).execute()
#             for file in response.get('files', []):
#                 files.append(file)
#             page_token = response.get('nextPageToken', None)
#             if page_token is None:
#                 break
#         file_count = len(files)
#         print(f'{file_count} modified files since last sync')
#         doc['last_sync'] = query_time
#         if file_count == 0:
#             col.update_one({}, {'$set': doc})
#             exit(0)
#         # Fix special caracters in file names (just had issues with the '/' yet)
#         for file in files:
#             if '/' in file['name']:
#                 files.remove(file)
#                 file['name'] = file['name'].replace('/', '-')
#                 files.append(file)
#     # Clone list to manage download progress
#     new_files = files.copy()
#     # Download files
#     for f in files:
#         try:
#             if doc.get('excludes'):
#                 if f['id'] in doc['excludes']:
#                     new_files.remove(f)
#                     continue
#             if f.get('parents'):
#                 right_dir = get_parent(f['parents'][0])
#             else:
#                 right_dir = FILES_PATH
#             if f['mimeType'] == 'application/vnd.google-apps.document':
#                 downl_doc(f['id'],
#                             path.join(right_dir, f['name']+'.docx'),
#                             'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
#             elif f['mimeType'] == 'application/vnd.google-apps.spreadsheet':
#                 downl_doc(f['id'],
#                         path.join(right_dir, f['name']+'.xlsx'),
#                         'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
#             elif f['mimeType'] == 'application/vnd.google-apps.drawing':
#                 downl_doc(f['id'],
#                         path.join(right_dir, f['name']+'.svg'),
#                         'image/svg+xml')
#             elif f['mimeType'] == 'application/vnd.google-apps.presentation':
#                 downl_doc(f['id'],
#                         path.join(right_dir, f['name']+'.pptx'),
#                         'application/vnd.openxmlformats-officedocument.presentationml.presentation')
#             elif f['mimeType'] == 'application/vnd.google-apps.form':
#                 print(f"\nFile '{path.join(right_dir, f['name'])}' is a Form")
#                 new_files.remove(f)
#                 continue
#             elif f['mimeType'] == 'application/vnd.google-apps.shortcut': # Just a shortcut
#                 new_files.remove(f)
#                 continue
#             elif f['mimeType'] == 'application/vnd.google-apps.folder': # Just a folder
#                 new_files.remove(f)
#                 continue
#             # Not a Google Document, so download normaly:
#             else:
#                 downl_doc(f['id'], path.join(right_dir, f['name']), doc=False)
#             new_files.remove(f)
#         except Exception as e:
#             exclude_link = f"{API}?exclude={f['id']}"
#             if 'too large' in str(e):
#                 msg = f"The file {path.join(right_dir, f['name'])} is too large to be exported by GDrive API.\nUse this link to exclude the file from drivedump:\n{exclude_link}\n\nSystem Error Message: \n{str(e)}"
#                 print(msg)
#                 send_mail(MAIL_ADMIN, 'Drive - Arquivo muito grande', msg)
#             elif 'Rate Limit Exceeded' in str(e):
#                 msg = f"Rate limit exceeded\n\nSystem Error Message: \n{str(e)}"
#                 print(msg)
#                 doc['pending_files'] = new_files
#                 col.update_one({}, {'$set': doc})
#                 send_mail(MAIL_ADMIN, 'Drive - Rate limit exceeded', msg)
#                 exit(0)
#             else:
#                 msg = f"Error to download file {path.join(right_dir, f['name'])}\nUse this link to exclude the file from drivedump:\n{exclude_link}\n\nSystem Error Message: \n{str(e)}"
#                 print(msg)
#                 send_mail(MAIL_ADMIN, 'Drive - Falha ao baixar arquivo', msg)

#     if len(new_files) == 0:
#         print(f'All {len(files)} files Downloaded.')
#         file_names = [x['name'] for x in files]
#         send_mail(MAIL_ADMIN, f'Drive - All {len(files)} files downloaded', '\n'.join(file_names))
#     else:
#         print(f'Remaining {len(new_files)} files to download')
#         file_names = [x['name'] for x in new_files]
#         send_mail(MAIL_ADMIN, f'Drive - Remaining {len(new_files)} files to download', '\n'.join(file_names))
#     doc['pending_files'] = new_files
#     col.update_one({}, {'$set': doc})

# if __name__ == '__main__':
#     drive = init_drive()
#     dump_drive(drive)


