#!/usr/bin/python
import os,sys
import json
import httplib2
import google_constants as constants
from googleapiclient import discovery

import oauth2client
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

DIRECTORY_API_CLIENT = None
DIRECTORY_API_CLIENT_VERSION = None


#
# These are the authorization scopes required
SCOPES = 'https://www.googleapis.com/auth/admin.directory.user.readonly','https://www.googleapis.com/auth/admin.directory.group.readonly','https://www.googleapis.com/auth/#admin.directory.group.member.readonly','https://www.googleapis.com/auth/cloud-platform.read-only','https://www.googleapis.com/auth/compute.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Admin Script API'



def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'admin-directory_v1-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials



#
# API at https://developers.google.com/admin-sdk/directory/v1/reference/
#
def directory_get_api_client(version = "directory_v1"):
    global DIRECTORY_API_CLIENT
    global DIRECTORY_API_CLIENT_VERSION

    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())

    if DIRECTORY_API_CLIENT == None or DIRECTORY_API_CLIENT_VERSION != version:
        DIRECTORY_API_CLIENT = discovery.build('admin', 'directory_v1', http=http)
        DIRECTORY_API_CLIENT_VERSION = version
    return DIRECTORY_API_CLIENT








#
# Returns a project resource object
# https://developers.google.com/resources/api-libraries/documentation/directory/v1/python/latest/directory_v1.projects.html#get
#
def directory_get_group(groupKey):
    return directory_get_api_client().group().get(groupKey = groupKey).execute()


#
# The projects.list() method specifies that there is a limit to the number of projects returned on each call
# A nextPageToken will be return in case the list has been truncated
#
def directory_get_groups(requestedPageSize = 200):

    service = directory_get_api_client()
    groups = []
    nextPageToken = None

    while True:

        result = service.groups().list(domain = "grbgcpdevops.net", maxResults=requestedPageSize, orderBy='email', pageToken=nextPageToken).execute()

        if 'groups' in result:
            groups.extend(result.get("groups"))

            if ('nextPageToken' not in result or result['nextPageToken'] is None): # No more pages
                return groups
            else: # There are more pages
                nextPageToken = result['nextPageToken']

        else: # No (more) groups found
            return groups


def directory_get_group_members(groupKey, requestedPageSize = 200):

    service = directory_get_api_client()
    members = []
    nextPageToken = None

    while True:

        result = service.members().list(groupKey=groupKey, maxResults=requestedPageSize, pageToken=nextPageToken).execute()

        if 'members' in result:
            members.extend(result.get("members"))

            if ('nextPageToken' not in result or result['nextPageToken'] is None): # No more pages
                return members
            else: # There are more pages
                nextPageToken = result['nextPageToken']

        else: # No (more) members found
            return members



def directory_get_users(requestedPageSize = 500):

    users = []
    nextPageToken = None

    while True:

        result = directory_get_api_client().users().list(domain="grbgcpdevops.net", maxResults=requestedPageSize, orderBy='email', pageToken=nextPageToken).execute()

        if 'users' in result:
            users.extend(result.get("users"))

            if ('nextPageToken' not in result or result['nextPageToken'] is None): # No more pages
                return users
            else: # There are more pages
                nextPageToken = result['nextPageToken']

        else: # No (more) users found
            return users
