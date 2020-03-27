#!/usr/bin/python
import sys
import re
import time
import json

import googleapiclient.discovery as discovery
from googleapiclient.errors import HttpError

from oauth2client.client import GoogleCredentials

# TODO oauth2client is deprecated. Use google.auth
#import google.auth
#from google.auth import compute_engine


#####################################################
#
#   GOOGLE CLOUDSQL COMMON FUNCTIONS AND CONSTANTS
#
####################################################

# Singleton style global variables
# Only one API client is stored at a time
CLOUDSQL_API_CLIENT = None
CLOUDSQL_API_CLIENT_VERSION = None

# [START cloudsql_get_api_client]
def cloudsql_get_api_client(version = "v1beta4"):
    global CLOUDSQL_API_CLIENT
    global CLOUDSQL_API_CLIENT_VERSION
    if CLOUDSQL_API_CLIENT == None or CLOUDSQL_API_CLIENT_VERSION != version:
        CLOUDSQL_API_CLIENT = discovery.build('sqladmin', version, credentials = GoogleCredentials.get_application_default())
        CLOUDSQL_API_CLIENT_VERSION = version
    return CLOUDSQL_API_CLIENT
# [END cloudsql_get_api_client]

###########################################
#
# INSTANCE FUNCTIONS
#
###########################################

# [START cloudsql_delete_instance]
def cloudsql_delete_instance(project, instanceName):
    return cloudsql_get_api_client().instances().delete(
        project=project,
        instance=instanceName).execute()
# [END cloudsql_delete_instance]


# [START cloudsql_list_instances]
def cloudsql_list_instances (project):
    items = []
    nextPageToken = None
    while True:
        result = {}
        try:
            result = cloudsql_get_api_client().instances().list(project=project, pageToken=nextPageToken).execute()  # maxResults is 500 by default
        except HttpError as e:
            print "[ERROR] HTTPError {0} Message:{1}".format(e.resp.status, json.loads(e.content)['error']['message'])
            raise e
        except:
            print "[ERROR] Unknown Error listing CloudSQL instances on project {0}".format(project)
            raise

        if 'items' in result:
            items = items + result['items']
            if ('nextPageToken' not in result or result['nextPageToken'] is None): # No more pages
                return items
            else: # There are more pages
                nextPageToken = result['nextPageToken']
        else: # No (more) VMs found
            return items
# [END cloudsql_list_instances]


# [START cloudsql_get_instance]
# Return an Operation resoruce JSON object.
def cloudsql_get_instance(project, instanceName):
    return cloudsql_get_api_client().instances().get(project=project, instance=instanceName).execute()
# [END cloudsql_get_instance]


#
# The Stop function is not available yet in the API
#
# [START cloudsql_stop_instance]
# Return an Operation resoruce JSON object.
#def cloudsql_stop_instance(project, instanceName):
#    return cloudsql_get_api_client().instances().stop(project=project, instance=instanceName).execute()
# [END cloudsql_stop_instance]


#
# The Start function is not available yet in the API
#
# [START cloudsql_start_instance]
# Return an Operation resoruce JSON object.
#def cloudsql_start_instance(project, instanceName):
#    return cloudsql_get_api_client().instances().start(project=project, instance=instanceName).execute()
# [END cloudsql_start_instance]





###########################################
#
# DATABASE FUNCTIONS
#
###########################################

# [START cloudsql_delete_database]
def cloudsql_delete_database(project, instanceName, databaseName):
    return cloudsql_get_api_client().databases().delete(
        project=project,
        instance=instanceName,
        database=databaseName).execute()
# [END cloudsql_delete_database]


# [START cloudsql_list_databases]
def cloudsql_list_databases (project, instanceName):
    items = []

    result = {}
    try:
        result = cloudsql_get_api_client().databases().list(project=project, instance=instanceName).execute()  # maxResults is 500 by default
    except HttpError as e:
        print "[ERROR] HTTPError {0} Message:{1}".format(e.resp.status, json.loads(e.content)['error']['message'])
        raise e
    except:
        print "[ERROR] Unknown Error listing CloudSQL databases on project {0} and instance {1}".format(project, instanceName)
        raise

    if 'items' in result:
        items = items + result['items']

    return items
# [END cloudsql_list_databases]


# [START cloudsql_get_database]
def cloudsql_get_database(project, instanceName, databaseName):
    return cloudsql_get_api_client().databases().get(project=project, instance=instanceName, database=databaseName).execute()
# [END cloudsql_get_database]
