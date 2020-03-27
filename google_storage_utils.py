#!/usr/bin/python
import sys
import re
import time
import os
import json
import httplib2
import google_constants as constants
from googleapiclient import discovery
from google.cloud import storage
import oauth2client
from oauth2client import client
from oauth2client.client import GoogleCredentials




####################################################
#
#   GOOGLE STORAGE COMMON FUNCTIONS
#
#  *************** This Library has not been developed yet
#
####################################################

STORAGE_API_CLIENT = None
STORAGE_API_CLIENT_VERSION = None

#
# API at https://developers.google.com/apis-explorer/#p/cloudresourcemanager/v1/
#
def storage_get_api_client(version = "v1"):
    global STORAGE_API_CLIENT
    global STORAGE_API_CLIENT_VERSION

    credentials = GoogleCredentials.get_application_default()

    if STORAGE_API_CLIENT == None or STORAGE_API_CLIENT_VERSION != version:
        STORAGE_API_CLIENT = discovery.build('storage', version = version, credentials = credentials)
        STORAGE_API_CLIENT_VERSION = version
    return STORAGE_API_CLIENT



def storage_list_buckets (storage, project, zone):
    storage_client = storage.Client()

    # Make an authenticated API request
    buckets = list(storage_client.list_buckets())
    print(buckets)
