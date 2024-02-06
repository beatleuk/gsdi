from __future__ import print_function
import httplib2
import os
import sys
import csv
import codecs

from operator import itemgetter, attrgetter
from apiclient import errors, discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

try:
    import argparse

    parent = argparse.ArgumentParser(parents=[tools.argparser])
    parent.add_argument("-f", "--folder_id", help="Enter folder ID to list")
    parent.add_argument("-c", "--csv_file_in", help="Enter a csv file to report against")
    flags = parent.parse_args()
except ImportError:
    flags = None

# This script is dervived from Googles own Google Drive API Python
# Quickstart and pulls together many of the reference samples.

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/dgdfl-secrets.json
SCOPES = 'https://www.googleapis.com/auth/drive.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Google Drive Folder List'


def get_credentials():
    """Gets valid user credentials from storage.
    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.
    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    client_secret = os.path.join(os.curdir, CLIENT_SECRET_FILE)
    if not client_secret:
        print('Follow the instructions in Step 1 on the following '
              'page:\nhttps://developers.google.com/drive/v3/web/quickstart/python')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'gdfl-secrets.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else:  # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials
FOLDERCOUNT = 0
FILECOUNT = 0
DEEPEST = 0

def process_folder(service,folder_id):
    try:
        folder = service.files().get(fileId=folder_id).execute()
        foldername = folder['name']
        drivetype = 'My Drive'
        print("Folder ID " + folder_id + " is a Google Drive Folder called: " + foldername + "please only use Shared Drive IDs")
        exit()
    except errors.HttpError as error:
        try:
            folder = service.drives().get(
                driveId=folder_id,
                useDomainAdminAccess='true').execute()
            foldername = folder['name']
            drivetype = 'Shared Drive'
            print("Folder ID " + folder_id + " is a Shared Drive named: " + foldername)
        except errors.HttpError as error:
            foldername = ''
            print(f"An error occurred: {error}")
            exit()

    if (sys.version_info < (3, 0)):
        if isinstance(foldername, str):
            foldername = unicode(foldername, "utf-8")

    if (sys.version_info < (3, 0)):
        print('Building CSV file output for {0}'.format(folder['name'].encode("utf-8")))
    else:
        print('Building CSV file output for {0}'.format(folder['name']))

    csv_file_name = 'GDFL-' + foldername + '.csv'
    CSV_DATA = [['folderPath','parentID','mimeType','itemtName','fileSize(MB)','itemID','itemURL']]
    folder_path = '/'

    get_folder(service, folder_id, CSV_DATA, folder_path)

    with open(csv_file_name, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(CSV_DATA)

    print('Created CSV file {0}'.format(csv_file_name))

def get_folder(service, folder_id, CSV_DATA, folder_path):
    """Get's the folders in the parent folder
    """
    global FOLDERCOUNT
    global FILECOUNT
    global DEEPEST
    page_token1 = ''
    while page_token1!=None:
        try:
            query1 = "'" + folder_id + "' in parents and trashed=false"
            results1 = service.files().list(
                q=query1,
                driveId=folder_id,
                corpora='drive',
                includeItemsFromAllDrives='true',
                supportsAllDrives='true',
                orderBy='folder,name',
                pageToken=page_token1,
                fields="nextPageToken, files(id, name, parents, quotaBytesUsed, webViewLink, iconLink, mimeType)").execute()
            
            items1 = results1.get('files', [])
            items1.sort(key=itemgetter('name'))
            if items1:
                for item1 in items1:
                    current_id = item1['id']
                    item1name = item1['name']
                    file_size = 0
                    if item1['mimeType'] == 'application/vnd.google-apps.folder':
                        sub_folder_path = folder_path + "/" + item1name
                        print("Processing folder " + sub_folder_path)
                        get_child_sub_folders(service, current_id, CSV_DATA, folder_id, sub_folder_path)
                    else:
                        if item1['quotaBytesUsed']:
                            file_size = round(int(item1['quotaBytesUsed']) / 1028,2)
                        ##print("Processing item " + item1name)
                        CSV_DATA.append([folder_path,folder_id,item1['mimeType'],item1name,file_size,current_id,item1['webViewLink']])
            page_token1 = results1.get('nextPageToken')

        except errors.HttpError as error:
            print('An error occurred: ' + error)

def get_child_sub_folders(service, parent_id, CSV_DATA, folder_id, sub_folder_path):
    """Get's the folders in the child folder
    """
    global FOLDERCOUNT
    global FILECOUNT
    global DEEPEST
    page_token2 = ''
    while page_token2!=None:
        try:
            query2 = "'" + parent_id + "' in parents and trashed=false"
            results2 = service.files().list(
                q=query2,
                driveId=folder_id,
                corpora='drive',
                includeItemsFromAllDrives='true',
                supportsAllDrives='true',
                orderBy='folder,name',
                pageToken=page_token2,
                fields="nextPageToken, files(id, name, parents, quotaBytesUsed, webViewLink, iconLink, mimeType)").execute()

            items2 = results2.get('files', [])
            items2.sort(key=itemgetter('name'))
            if items2:
                for item2 in items2:
                    child_id = item2['id']
                    childname = item2['name']
                    file_size = 0
                    if item2['mimeType'] == 'application/vnd.google-apps.folder':
                        child_folder_path = sub_folder_path + "/" + childname
                        print("Processing folder " + child_folder_path)
                        get_child_sub_folders(service, child_id, CSV_DATA, folder_id, child_folder_path)
                    else:
                        if item2['quotaBytesUsed']:
                            file_size = round(int(item2['quotaBytesUsed']) / 1028,2)
                        ##print("Processing child item " + childname)
                        CSV_DATA.append([sub_folder_path,parent_id,item2['mimeType'],childname,file_size,child_id,item2['webViewLink']])

            page_token2 = results2.get('nextPageToken')

        except errors.HttpError as error:
            print('An error occurred: %s' % error)

def main():
    """Google Shared Drive Inventory
    Uses Google Drive API to get the parent folder
    Gets the parent folder specified in args or in the CSV file provided
    Calls the function to get sub folders and loops through all child folders.
    Produces a csv file output for each Shared Drive.
    """
    if not (flags.folder_id or flags.csv_file_in):
        print(f"You must specify a Shared Drive ID or CSV file")
        exit()

    foldername = ''
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('drive', 'v3', http=http)

    if flags.csv_file_in:
        with open(flags.csv_file_in, newline='') as csvFile_In:
            sharedDrives = csv.DictReader(csvFile_In)
            for sharedDrive in sharedDrives:
                print(sharedDrive['SharedDriveName'], sharedDrive['SharedDriveID'])
                process_folder(service,sharedDrive['SharedDriveID'])
    else:
        process_folder(service,flags.folder_id)

if __name__ == '__main__':
    main()
