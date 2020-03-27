#!/usr/bin/python
import sys
import re
import time
import json
import googleapiclient.discovery as discovery
from googleapiclient.errors import HttpError

#####################################################
#
#   GOOGLE COMPUTE COMMON FUNCTIONS AND CONSTANTS
#
####################################################
PET_OR_CATTLE_LABEL="pet_or_cattle"
PET_VALUE="pet"
CATTLE_VALUE="cattle"

# Singleton style global variables
# Only one API client is stored at a time
COMPUTE_API_CLIENT = None
COMPUTE_API_CLIENT_VERSION = None


COMPUTE_START_OPERATION = "START"
COMPUTE_STOP_OPERATION = "STOP"
COMPUTE_ALLOWED_OPERATIONS = [COMPUTE_START_OPERATION, COMPUTE_STOP_OPERATION]

# Compute Zone Operation Statuses
OPERATION_DONE = "DONE"
OPERATION_RUNNING = "RUNNING"
OPERATION_PENDING = "PENDING"

# Compute Instace Statuses
# PROVISIONING, STAGING, RUNNING, STOPPING, STOPPED, SUSPENDING, SUSPENDED, and TERMINATED.
PROVISIONING = "PROVISIONING"
STAGING = "STAGING"
RUNNING = "RUNNING"
STOPPING = "STOPPING"
STOPPED = "STOPPED"
SUSPENDING = "SUSPENDING"
SUSPENDED = "SUSPENDED"
TERMINATED = "TERMINATED"


# [START compute_get_api_client]
def compute_get_api_client(version = "v1"):
    global COMPUTE_API_CLIENT
    global COMPUTE_API_CLIENT_VERSION
    if COMPUTE_API_CLIENT == None or COMPUTE_API_CLIENT_VERSION != version:
        COMPUTE_API_CLIENT = discovery.build('compute', version)
        COMPUTE_API_CLIENT_VERSION = version
    return COMPUTE_API_CLIENT
# [END compute_get_api_client]


#
# Returns the Compute Metadata for the Project
# https://developers.google.com/resources/api-libraries/documentation/compute/v1/python/latest/compute_v1.projects.html#get
#
def compute_get_project(projectId):
    return compute_get_api_client().projects().get(project = projectId).execute()


# [START compute_delete_instance]
def compute_delete_instance(project, zone, name):
    return compute_get_api_client().instances().delete(
        project=project,
        zone=zone,
        instance=name).execute()
# [END compute_delete_instance]


# [START compute_list_instances]
def compute_list_instances (project, zone):
    items = []
    nextPageToken = None
    while True:
        result = {}
        try:
            result = compute_get_api_client().instances().list(project=project, zone=zone, pageToken=nextPageToken).execute()  # maxResults is 500 by default
        except HttpError as e:
            print "[ERROR] HTTPError {0} Message:{1}".format(e.resp.status, json.loads(e.content)['error']['message'])
            raise e
        except:
            print "[ERROR] Unknown Error listing VM on project {0} in zone {1}".format(project, zone)
            raise

        if 'items' in result:
            items = items + result['items']
            if ('nextPageToken' not in result or result['nextPageToken'] is None): # No more pages
                return items
            else: # There are more pages
                nextPageToken = result['nextPageToken']
        else: # No (more) VMs found
            return items
# [END compute_list_instances]


# [START compute_stop_instance]
# Return an Operation resoruce JSON object.
def compute_stop_instance(project, zone, instanceName):
    return compute_get_api_client().instances().stop(project=project, zone=zone, instance=instanceName).execute()
# [END compute_stop_instance]


# [START compute_start_instance]
# Return an Operation resoruce JSON object.
def compute_start_instance(project, zone, instanceName):
    return compute_get_api_client().instances().start(project=project, zone=zone, instance=instanceName).execute()
# [END compute_start_instance]


# [START compute_perform_operation_on_instance]
# Return an Operation resoruce JSON object.
def compute_perform_operation_on_instance(project, zone, instanceName, operationName, targetOperationStatus = OPERATION_DONE):

    if operationName not in COMPUTE_ALLOWED_OPERATIONS:
        print "[ERROR] Operation {0} is not allowed".format(operation)
        return False

    print "[INFO] Compute Instance {0} - Invoking {1} operation".format(instanceName, operationName),#The comma avoids a new line after the print
    if operationName == COMPUTE_START_OPERATION:
        operationResource = compute_start_instance(project, zone, instanceName)
    elif operationName == COMPUTE_STOP_OPERATION:
        operationResource = compute_stop_instance(project, zone, instanceName)

    result = compute_wait_for_operation(project, zone, operationResource['name'], targetOperationStatus)

    print "\n[INFO] Compute Instance {0} - Operation: {1} - Status: {2}".format(instanceName, operationName, result["status"])

    # Check the current status of the VM
    if result["status"] == OPERATION_DONE:
        instanceResource = compute_get_instance(project, zone, instanceName)
        print "[INFO] Compute Instance {0} - Status: {1}".format(instanceName, instanceResource['status'])

    return True



# [END compute_perform_operation_on_instance]



# [START compute_get_instance]
# Return an Operation resoruce JSON object.
def compute_get_instance(project, zone, instanceName):
    return compute_get_api_client().instances().get(project=project, zone=zone, instance=instanceName).execute()
# [END compute_get_instance]



# [START compute_set_instance_label]
def compute_set_instance_label(project, zone, instanceName, newLabelBody):
    return compute_get_api_client().instances().setLabels(project=project, zone=zone, instance=instanceName, body=newLabelBody).execute()
# [END compute_set_instance_label]





# [START compute_set_disk_label]
def compute_set_disk_label(project, zone, diskName, newLabelBody):
    return compute_get_api_client().disks().setLabels(project=project, zone=zone, resource=diskName, body=newLabelBody).execute()
# [END compute_set_disk_label]


# [START compute_list_disks]
def compute_list_disks (project, zone):
    items = []
    nextPageToken = None
    while True:
        result = compute_get_api_client().disks().list(project=project, zone=zone, pageToken=nextPageToken).execute()  # maxResults is 500 by default
        if 'items' in result:
            items = items + result['items']
            if ('nextPageToken' not in result or result['nextPageToken'] is None): # No more pages
                return items
            else: # There are more pages
                nextPageToken = result['nextPageToken']
        else: # No (more) VMs found
            return items
# [END compute_list_disks]



def compute_get_metadata_value(project, zone, instanceName, metadataKey):

    itemValue = None
    instanceResource = compute_get_instance(project, zone, instanceName)

    if "items" in instanceResource['metadata']:
        for item in instanceResource['metadata']['items']:
            if item["key"] == metadataKey:
                itemValue = item["value"]

    return itemValue





# [START compute_wait_for_operation]
def compute_wait_for_operation(project, zone, operation, targetOperationStatus = OPERATION_DONE):
    while True:
        sys.stdout.write('.')
        sys.stdout.flush()
        result = compute_get_api_client().zoneOperations().get(
            project=project,
            zone=zone,
            operation=operation).execute()

        #if "warnings" in result and len(result['warnings'])>0:
        #    for warning in result['warnings']:
        #        print "\n[DEBUG] Operation Warning: {0} ".format(warning['message'])

        if result['status'] == OPERATION_DONE or result['status'] == targetOperationStatus :
        #    print "\n[DEBUG] Operation Status: {0} ".format(result['status'])
            if 'error' in result:
                raise Exception(result['error'])
            return result

        time.sleep(5)
# [END compute_wait_for_operation]
