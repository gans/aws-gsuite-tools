from __future__ import print_function
import pickle, os, io
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from apiclient.http import MediaIoBaseDownload

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive']

folders = {
'201501': 'lalala-hash-lalala-hash-folder',
'201502': 'lalala-hash-lalala-hash-folder',
'201503': 'lalala-hash-lalala-hash-folder',
'201504': 'lalala-hash-lalala-hash-folder',
'201505': 'lalala-hash-lalala-hash-folder',
'201506': 'lalala-hash-lalala-hash-folder',
'201507': 'lalala-hash-lalala-hash-folder',
'201508': 'lalala-hash-lalala-hash-folder',
'201509': 'lalala-hash-lalala-hash-folder',
'201510': 'lalala-hash-lalala-hash-folder',
'201511': 'lalala-hash-lalala-hash-folder',
'201512': 'lalala-hash-lalala-hash-folder',
    }

def getService():
    """Shows basic usage of the Drive v3 API.
    Prints the names and ids of the first 10 files the user has access to.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('drive', 'v3', credentials=creds)
    return service

def getMainFolders(h):
    service = getService()
    value = h
    results = service.files().list(
            q="'{}' in parents".format(value),
            fields="nextPageToken, files(id, name)").execute()
    items = results.get('files', [])
    for i in items:
        print('{} {}'.format(i['name'].encode('utf-8'), i['id']))

def main():
    service = getService()
    errors = []
    for key, value in folders.items():
        key_year = key[:4]
        results = service.files().list(
            q="'{}' in parents".format(value),
            fields="nextPageToken, files(id, name)").execute()
        items = results.get('files', [])

        if not items:
            print('No files found.')
        else:
            day_file = {}
            for item in items:
                item_name = item['name']
                if not item_name.startswith(key) or len(item_name) > 12:
                    continue
                name = item_name.replace(key_year, '').split('.')[0]
                if len(name) == 3:
                    name = '{}{}{}'.format(name[:2],'0', name[2:])
                folder_name = '{}{}'.format(key_year, name)
                if not os.path.exists(folder_name):
                    os.mkdir(folder_name)
                if not day_file.get(name):
                    day_file[name] = ['', '']
                if item_name.lower().endswith('.pdf'):
                    day_file[name][0] = item['id']
                if item_name.lower().endswith('.txt'):
                    day_file[name][1] = item['id']
                #print(u'{0} ({1})'.format(item['name'], item['id']))

            for dt, files in day_file.items():
                print(key_year, dt)
                if files[0] and files[1]:
                    #continue
                    # pdf
                    request = service.files().get_media(fileId=files[0])
                    #fh = io.BytesIO()
                    fh = open('{}{}/original.pdf'.format(key_year, dt), 'w')
                    downloader = MediaIoBaseDownload(fh, request)
                    done = False
                    while done is False:
                        status, done = downloader.next_chunk()
                    fh.close()

                    # cadernos
                    request = service.files().get_media(fileId=files[1])
                    #fh = io.BytesIO()
                    fh = open('{}{}/cadernos.txt'.format(key_year, dt), 'w')
                    downloader = MediaIoBaseDownload(fh, request)
                    done = False
                    while done is False:
                        status, done = downloader.next_chunk()
                    fh.close()
                else:
                    errors.append('error : {} {}'.format(dt, files))

    print(' error *' * 20)
    print(errors)

            

if __name__ == '__main__':
    main()
    #getMainFolders('lalala-hash-lalala-hash-folder')
