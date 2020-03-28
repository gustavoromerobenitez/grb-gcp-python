#!/usr/bin/python
import os,sys
import argparse
import json
import oauth2client
from oauth2client.client import GoogleCredentials
from google.cloud import bigquery
from googleapiclient import discovery

# The common utils library is supposed to be located at the root of that path
# This is needed to find the google_resourcemanager_common_utils module since this Unit test is not within the same module
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)

import google_cloudresourcemanager_utils as utils


def get_datasets():
    _datasets = list()

    projects = utils.cloudresourcemanager_get_all_projects()
    if projects == None:
        return

    credentials = GoogleCredentials.get_application_default()
    service = discovery.build('bigquery', 'v2', credentials=credentials)
    api_service = service.datasets()

    for project in projects:
        request = api_service.list(projectId=project['projectId'])

        while request is not None:
            try:
                results = request.execute()
            except:
                break
            datasets = results.get('datasets')
            if datasets:
                for dataset in datasets:
                    project_id, dataset_id = dataset['id'].split(':')
                    d = {u'id': dataset_id,
                         u'projectId': project_id,
                         u'location': dataset['location']}
                    _datasets.append(d)
            request = api_service.list_next(request, results)

    return _datasets



def print_datasets():
    datasets = get_datasets()
    client = bigquery.Client()

    for dataset in datasets:
        dataset_id = "{}.{}".format(dataset['projectId'], dataset['id'])
        blah = client.get_dataset(dataset_id)
        entries = list(blah.access_entries)
        print('{0}|{1}|{2}'.format(dataset['projectId'],dataset['id'],dataset['location']))
        for entry in entries:
            print(entry)

print_datasets()
