#!/bin/env python

#
# Report on service accounts in projects
# can report on Google Managed or User Managed Service Acccounts
#
import argparse
from googleapiclient.errors import HttpError
from googleapiclient import discovery
from oauth2client.client import GoogleCredentials
import os.path
import sys
from pprint import pprint # Useful for printing out resources in full, e.g. pprint(key)

# The libraries are located one level above the scripts folder
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)

import google_cloudresourcemanager_utils as resourceManagerUtils
import googleapiclient
import google_constants as constants




debug = False
#debug = True


# [START run]
def main(projectsArgumentList, region, zone, keytype, serviceaccount, serviceaccountmail, showkey, brief, exclusions):

    projectList=[]


    if debug:
        print("brief: " + str(brief))
        print("exclusions: " + str(exclusions))

    if debug and exclusions is not None:
        print("exclusions: " + str(exclusions))
        print("exclusion list:")

    if exclusions is not None and not os.path.exists(exclusions):
        print("filename" + exclusions  + "does not exist")
        sys.exit(1)

    elif exclusions is not None:
		    exclusion_list = [line.rstrip('\n') for line in open(exclusions)]

    if debug and exclusions is not None:
        for l in exclusion_list:
		        print(l)

    print "\n\n[INFO] ================================================================================================"

    if "all" in projectsArgumentList:

        print "[INFO] Projects with user managed keys associated with service accounts and their service accounts/keys"

        projects = resourceManagerUtils.cloudresourcemanager_get_projects( requestedPageSize = 0, projectFilter = "Name:grb-*")
        for project in projects:
            if project['lifecycleState'] != 'DELETE_REQUESTED':
                projectList.append(project['projectId'])
    else:
        projectList = projectsArgumentList
        print "[INFO] Projects provided: {0}".format(projectList)
        print("key report for key type: " + keytype)

    print "[INFO] ===================================================================================================="

    for project in projectList:

        try:
            project_res = resourceManagerUtils.cloudresourcemanager_get_project(project)

        except HttpError as e:
            print("ERROR getting project resource for project: " + project)
            print("HTTP status code: " + str(e.resp.status))
            if debug:
                print(e.content)
            print("Request: " + e.uri)
            continue

        if debug:
            print project_res
            print("projectid is: " + project_res['projectId'])
            print("name is: " + project_res['name'])
            print("lifecycleState is: " + project_res['lifecycleState'])


        credentials = GoogleCredentials.get_application_default()

        service = googleapiclient.discovery.build('iam', 'v1', credentials=credentials)

        try:
            service_accounts = service.projects().serviceAccounts().list(name='projects/' + project_res['projectId']).execute()

        except HttpError as e:
            print("ERROR retrieving service accounts for project: " + project + " project resource: ")
            pprint(project_res)
            print("name is: " + project_res['name'])
            print("lifecycleState is: " + project_res['lifecycleState'])
            print("HTTP status code: " + str(e.resp.status))
            if debug:
                print(e.content)
            print("Request: " + e.uri)
            continue

        if 'accounts' in service_accounts:
            for account in service_accounts['accounts']:
                if debug:
                    print('Name: ' + account['name'])
                    print('Email: ' + account['email'])
                    print(' ')

                full_name = "projects/" +  project_res['projectId'] + "/serviceAccounts/" + account['email']

                if debug:
                    print('project full_name: ' + full_name)

                try:
                    keys = service.projects().serviceAccounts().keys().list(name=full_name,keyTypes=keytype).execute()

                except HttpError as e:
                    print("ERROR retrieving service account keys for project: " + project + " and service account " + full_name)
                    print("HTTP status code: " + str(e.resp.status))
                    if debug:
                        print(e.content)
                    print("Request: " + e.uri)
                    continue


                if keys:
                    key_names = []
                    for key in keys['keys']:
                        key_names.append(key['name'])
                    if not brief:
                        print "\n\n[INFO] ======================================================================================"
                        print "[INFO] Project: {0}".format(project)
                        print "[INFO] Zone: {0}".format(zone)
                        print
                    if serviceaccount and not brief:
                        print('Service Account Name: ' + account['name'])
                    if serviceaccountmail and not brief:
                        print('Email: ' + account['email'])
                    if showkey:
                        if exclusions is not None:
                            for remaining_key in list(set(key_names) - set(exclusion_list)):
                                print('Key: ' + key['name'])
                                # need to look up key by name to get details
                                print('Key validBeforeTime: ' + key['validBeforeTime'])
                                print('Key validAfterTime: ' + key['validAfterTime'])
                                print('Key keyAlgorithm: ' + key['keyAlgorithm'])
                                print('')
                        else:
                            for key in keys['keys']:
                                print('Key: ' + key['name'])
                                print('Key validBeforeTime: ' + key['validBeforeTime'])
                                print('Key validAfterTime: ' + key['validAfterTime'])
                                print('Key keyAlgorithm: ' + key['keyAlgorithm'])
                                print('')
                    if brief:
                        if exclusions is not None:
                            for remaining_key in list(set(key_names) - set(exclusion_list)):
                                print(project + '|' + account['name'] + '|' + remaining_key)
                        else:
                            for key in keys['keys']:
                                print(project + '|' + account['name'] + '|' + key['name'])
                    if not brief:
                        print "[INFO] ======================================================================================"
        else:
            if not brief:
                print("no service accounts found for project" + project_res['projectId'])



if __name__ == '__main__':
    parser = argparse.ArgumentParser( description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-p','--projects', required=True, metavar='project', nargs='+', help='List of Google Cloud projects where the actions will be performed. Use "-p all" to select all')
    parser.add_argument('-z','--zone', default='europe-west1-b', help='Optional Compute Engine zone where the actions will be performed.')
    parser.add_argument('-r','--region', default='europe-west1', help='Optional Compute Engine Region where the actions will be performed.')
    parser.add_argument('-t','--keytype', default="USER_MANAGED", help='Optional key type to report on, KEY_TYPE_UNSPECIFIED, USER_MANAGED or SYSTEM_MANAGED - defaults to USER_MANAGED.')
    parser.add_argument('-s','--serviceaccount', default=False, help='Optional display service account name that keys are associated with.', action="store_true")
    parser.add_argument('-m','--serviceaccountmail', default=False, help='Optional display service account email that keys are associated with.', action="store_true")
    parser.add_argument('-k','--showkey', default=False, help='Optional display key that matches keytype.', action="store_true")
    parser.add_argument('-b','--brief', default=False, help='brief output format', action="store_true")
    parser.add_argument('-e','--exclusions', help='file listing service account keys to exclude from reporting')
    args = parser.parse_args()
    main(args.projects, args.region, args.zone, args.keytype, args.serviceaccount, args.serviceaccountmail, args.showkey, args.brief, args.exclusions)
# [END run]
