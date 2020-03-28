#!/usr/bin/python
#
# pip install --upgrade google-api-python-client
# to run:
# ./user-audit.py --noauth_local_webserver --report users
#
# IF redirecting output to a file and using python2 invoke as:
# PYTHONIOENCODING=UTF-8 ./user-audit.py --report users > users
#
# based on code from
# https://developers.google.com/admin-sdk/directory/v1/quickstart/python
#

from __future__ import print_function
import httplib2
import os
from time import sleep
from time import strftime
import re
import sys
from pprint import pprint
import json
from googleapiclient import discovery

import oauth2client
from oauth2client import tools
from oauth2client.file import Storage
from oauth2client import client
from oauth2client.client import GoogleCredentials

#
# The common resourcemanager_utils library is supposed to be located in the parent directory
# This is needed to find the resourcemanager_utils module since it is not within the same module
#
import inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)
import google_cloudresourcemanager_utils as resourcemanager_utils
import google_directory_utils as directory_utils
import google_compute_utils as compute_utils
import google_storage_utils as storage_utils



def write_stderr(message):
    print(message, file=sys.stderr)

try:
    import argparse
    parser = argparse.ArgumentParser(parents=[tools.argparser])
    parser.add_argument('--report', required='True', choices=['groups', 'groupsusers', 'iam', 'projects', 'users',
                                                              'usersgroups', 'folders', 'projectowners', 'ip_audit',
                                                              'enabled_apis', 'local_accounts', 'buckets', 'datasets',
                                                              'compute'])
    parser.add_argument('--format', choices=['smart'])
    flags = parser.parse_args()
except ImportError:
    flags = None




def print_groups():
    groups = directory_utils.directory_get_groups()
    if not groups:
        print('No Groups in the domain.')
    else:
        for group in groups:
            print('{0}|({1})|{2}'.format(group['email'], group['name'], group['directMembersCount']))


def print_groups_users():

    groups = directory_utils.directory_get_groups()
    if not groups:
        print('No Groups in the domain.')
    else:
        print("[DEBUG] # of Groups: {0}".format(len(groups)))

        for group in groups:
            print('{:_<40}'.format(''))
            print('{0}|({1})|{2}'.format(group['email'], group['name'], group['directMembersCount']))
            print('{:_<40}'.format(''))

            members = directory_utils.directory_get_group_members(groupKey = group['email'])

            if members:
                for member in members:
                    print('{0}|{1}|{2}'.format(member.get('email', '(No email address)'), member.get('type', 'UNKNOWN'), member.get('status', 'UNKNOWN')))



def print_users():

    users = directory_utils.directory_get_users()
    if not users:
        print('No users in the domain.')
    else:
        if(flags.format == 'smart'):
            current_time = strftime('%Y-%m-%d %H:%M:%S')
            for user in users:
                if(user.get('suspended','') == True):
                   continue
                else:
                   print(u'{0}|{1}|{2}|{3}|{4}|{5}|{6} {7}'.format(current_time,
                                                       'GCP_BIGQUERY',
                                                       user['primaryEmail'],
                                                       user.get('lastLoginTime', '')[:-1],
                                                       user.get('creationTime', '')[:-1],
                                                       '',
                                                       user.get('name', '').get('givenName', ''),
                                                       user.get('name', '').get('familyName', '')))

        else:
            for user in users:
                print(u'{0}|{1}|{2}|{3}|{4}|{5}'.format(user.get('id', 'None'),
                                                        user['primaryEmail'],
                                                        user.get('name', '').get('givenName', ''),
                                                        user.get('name', '').get('familyName', ''),
                                                        user.get('lastLoginTime', ''),
                                                        user.get('suspended', '')))


def list_instances ( project, zone):
    items = []
    nextPageToken = None
    while True:
        result = compute_utils.compute_get_api_client().instances().list(project=project, zone=zone, pageToken=nextPageToken).execute() # maxResults is 500 by default
        if 'items' in result:
            items = items + result['items']
            if ('nextPageToken' not in result or result['nextPageToken'] is None): # No more pages
                return items
            else: # There are more pages
                nextPageToken = result['nextPageToken']
                #print "[DEBUG] NextPageToken:{0}".format(nextPageToken)
        else: # No (more) VMs found
            return items




def get_self_created_service_accounts():
    service_accounts = set()
    user_accounts = set()

    projects = resourcemanager_utils.cloudresourcemanager_get_all_projects()
    if not projects:
        print('No projects Found.')
    else:

        # we're looking for service accounts that are not created by google. They have a special email address format
        for project in projects:
            # non google created service account format
            regex = u'serviceAccount:.*' + project['projectId'] + u'.iam.gserviceaccount.com'

            bindings = resourcemanager_utils.cloudresourcemanager_get_project_iam_bindings(project['projectId'])
            for binding in bindings:
                for member in binding['members']:
                    if(re.search(regex, member)):
                        service_accounts.add(member)
                    else:
                        # check this is a user first or we'll catch all the service accounts too
                        if(re.search('^user:', member)):
                            user_accounts.add(member)

    return service_accounts, user_accounts



def print_local_accounts():

    service_accounts, user_accounts = get_self_created_service_accounts()
    current_time = strftime('%Y-%m-%d %H:%M:%S')

    for service_account in service_accounts:
        print('{0}|{1}|{2}|{3}|{4}|{5}|{6}|{7}|{8}|{9}'.format(current_time,
                                                           'GCP-BIGQUERY',
                                                           service_account[15:],
                                                           "",
                                                           "",
                                                           "",
                                                           "",
                                                           "",
                                                           "",
                                                           ""))

    for user in user_accounts:
        print('{0}|{1}|{2}|{3}|{4}|{5}|{6}|{7}|{8}|{9}'.format(current_time,
                                                           'GCP-BIGQUERY',
                                                           user[5:],
                                                           "",
                                                           "",
                                                           "",
                                                           "",
                                                           "",
                                                           "",
                                                           ""))

def get_iam_permissions():
    projects = resourcemanager_utils.cloudresourcemanager_get_all_projects()
    if not projects:
        print('No projects Found.')
    else:

        for project in projects:
            print('{0}'.format(project['projectId']))
            bindings = resourcemanager_utils.cloudresourcemanager_get_project_iam_bindings(project['projectId'])
            for binding in bindings:
                print('  {0}'.format(binding['role']))
                for member in binding['members']:
                    print('    {0}'.format(member))


def get_users_groups():
    users = directory_utils.directory_get_users()
    groups = directory_utils.directory_get_groups()
    userdict = dict()

    # create a dictionary of all users with an empty set of group membership
    for user in users:
        userdict[user['primaryEmail']] = set()

    for group in groups:
#        print('{:_<40}'.format(''))
#        print('{0}|({1})|{2}'.format(group['email'], group['name'], group['directMembersCount']))
#        print('{:_<40}'.format(''))
        members = directory_utils.directory_get_group_members(groupKey=group['email'])
        if members:
            for member in members:
                email = member.get('email', '(No email address)')
                try:
                    curr_groups = userdict[email]
                except KeyError:
                    userdict[email] = set()
                    curr_groups = userdict[email]

                curr_groups.add('{0}|{1}'.format(group['name'],group['email']))
                userdict[email] = curr_groups

    for user in userdict:
        print('{0}'.format(user))
        groups = userdict[user]
        for group in groups:
            print('  {0}'.format(group))




def get_project_owners():
    projects = resourcemanager_utils.cloudresourcemanager_get_all_projects()
    if not projects:
        print('No projects Founds.')
    else:
        for project in projects:
            print('{0}|{1}'.format(project['projectId'],project['name']))

            bindings = resourcemanager_utils.cloudresourcemanager_get_project_iam_bindings(project['projectId'])
            for binding in bindings:
                if binding['role'] == 'roles/owner':
                    print('  {0}'.format(binding['role']))
                    for member in binding['members']:
                        print('    {0}'.format(member))





def print_folders(parent=None, indent=0, results=list()):
    folders = resourcemanager_utils.cloudresourcemanager_get_folders(parent)
    if folders == None:
        return
    for folder in folders:
        folder['indent'] = indent
        results.append(folder)
        print_folders(parent=folder['name'], indent=indent+1, results=results)
    return results


def folders():
    print('name,folder_id,parent_id')
    results=print_folders(parent='organizations/660825140170', results=list())
    for folder in results:
        print('{0:>{indent}}"{1}",{2},{3}'.format("", folder['displayName'], folder['name'], folder['parent'], indent=folder['indent']*2))


def ip_aggregated_audit():
    """Uses the aggregatedList method to get all regions for all projects
    """
    projects =  resourcemanager_utils.cloudresourcemanager_get_all_projects()
    for project in projects:
        if(project['lifecycleState'] == 'ACTIVE'):
            regions = dict()
            address_service = compute_utils.compute_get_api_client().addresses()

            request = address_service.aggregatedList(project=project['projectId'],
                                                      fields='items')
            while request is not None:
                try:
                    results = request.execute()
                except:
                    # this usually happens because compute engine is not enabled so we can ignore the error
                    # write_stderr(results)
                    break
                regions.update(results.get('items'))

                request = address_service.list_next(request, results)
            for region in regions:
                addresses = regions[region].get('addresses')
                if(addresses):
                    for address in addresses:
                        print('{0},{1},{2},{3},{4},{5}'.format(project['projectId'], region, address.get('address'), address.get('addressType'), address.get('name'), address.get('status')))



def get_enabled_apis():
    projects = resourcemanager_utils.cloudresourcemanager_get_all_projects()
    if projects == None:
        return

    credentials = GoogleCredentials.get_application_default()
    service = discovery.build('serviceusage', 'v1beta1', credentials = credentials)
    api_service = service.services()

    for project in projects:
        if(project['lifecycleState'] == 'ACTIVE'):
            request = api_service.list(parent='projects/' + project['projectId'])

            while request is not None:
                try:
                    results = request.execute()
                except:
                    break
                for service in results['services']:
                    print(project['projectId'] + ',' + service['config']['name'] + ',' + service['state'])

                request = api_service.list_next(request, results)
        # yes, this sleep is required to stop breaking the API call limit
        sleep(10)


def get_buckets():

    _buckets = list()

    projects = resourcemanager_utils.cloudresourcemanager_get_all_projects()
    if projects == None:
        return


    for project in projects:

        api_service = storage_utils.storage_get_api_client().buckets()
        request = api_service.list(project=project['projectId'])

        while request is not None:
            try:
                results = request.execute()
            except:
                break
            buckets = results.get('items')
            if buckets:
                for bucket in buckets:
                    b = {u'projectId': project['projectId'],
                         u'id': bucket['id'],
                         u'location': bucket['location'],
                         u'updated': bucket['updated'],
                         u'timeCreated': bucket['timeCreated'],
                         u'storageClass': bucket['storageClass']}
                    _buckets.append(b)

            request = api_service.list_next(request, results)

    return _buckets




def print_buckets():
    buckets = get_buckets()

    if buckets:
        for bucket in buckets:
            print('{0}|{1}|{2}|{3}|{4}|{5}'.format(bucket['projectId'],
                                                   bucket['id'],
                                                   bucket['location'],
                                                   bucket['timeCreated'],
                                                   bucket['updated'],
                                                   bucket['storageClass']))


def get_datasets():
    _datasets = list()

    projects = resourcemanager_utils.cloudresourcemanager_get_all_projects()
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

    for dataset in datasets:
        print('{0}|{1}|{2}'.format(dataset['projectId'],dataset['id'],dataset['location']))



def get_zones(project_id):

    _zones = list()

    api_service = compute_utils.compute_get_api_client().zones()

    request = api_service.list(project=project_id)
    while request is not None:
        try:
            results = request.execute()
        except:
            break
        zones = results.get('items')
        if zones:
            for zone in zones:
                _zones.append(zone['name'])
        request = api_service.list_next(request, results)

    return _zones



def get_compute_instances():
    _instances = list()
    projects = resourcemanager_utils.cloudresourcemanager_get_all_projects()

    if projects == None:
        return

    api_service = compute_utils.compute_get_api_client().instances()
    for project in projects:
        zones = get_zones(project['projectId'])
        for zone in zones:
            request = api_service.list(project=project['projectId'], zone=zone)
            while request is not None:
                try:
                    results = request.execute()
                    instances = results.get('items')
                    for instance in instances:
                        print('{0}|{1}|{2}|{3}'.format(project['projectId'], zone, instance['name'], instance['status']))
                except:
                    break

                request = api_service.list_next(request, results)

    return _instances


def main():
    exit()

if __name__ == '__main__':
    switcher = {
        'users': print_users,
        'groups': print_groups,
        'groupsusers': print_groups_users,
        'projects': resourcemanager_utils.cloudresourcemanager_print_all_projects,
        'iam': get_iam_permissions,
        'usersgroups': get_users_groups,
        'folders': folders,
        'projectowners': get_project_owners,
        'ip_audit': ip_aggregated_audit,
        'enabled_apis': get_enabled_apis,
        'local_accounts': print_local_accounts,
        'buckets': print_buckets,
        'datasets': print_datasets,
        'compute': get_compute_instances
    }

    func = switcher.get(flags.report)
    func()
