#!/usr/bin/python
import json
import httplib2
import google_constants as constants
from googleapiclient import discovery

from oauth2client.client import GoogleCredentials

import google_directory_utils as directory_utils

CLOUDRESOURCEMANAGER_API_CLIENT = None
CLOUDRESOURCEMANAGER_API_CLIENT_VERSION = None

#
# API at https://developers.google.com/apis-explorer/#p/cloudresourcemanager/v1/
#
def cloudresourcemanager_get_api_client(version = "v1"):
    global CLOUDRESOURCEMANAGER_API_CLIENT
    global CLOUDRESOURCEMANAGER_API_CLIENT_VERSION

    if CLOUDRESOURCEMANAGER_API_CLIENT == None or CLOUDRESOURCEMANAGER_API_CLIENT_VERSION != version:

        if (version == "v2"):
            credentials = directory_utils.get_credentials()
            http = credentials.authorize(httplib2.Http())
            CLOUDRESOURCEMANAGER_API_CLIENT = discovery.build('cloudresourcemanager', version = version, http = http)

        else:
            credentials = GoogleCredentials.get_application_default()
            CLOUDRESOURCEMANAGER_API_CLIENT = discovery.build('cloudresourcemanager', version = version, credentials = credentials)

        CLOUDRESOURCEMANAGER_API_CLIENT_VERSION = version

    return CLOUDRESOURCEMANAGER_API_CLIENT



#
# Returns all folders under a specified parent
#
def cloudresourcemanager_get_folders(parent, requestedPageSize = 0):

    service = cloudresourcemanager_get_api_client(version = "v2")
    folders = []
    nextPageToken = None

    while True:

        result = service.folders().list(parent = parent, pageSize=requestedPageSize, pageToken=nextPageToken).execute()

        if 'folders' in result:
            folders.extend(result['folders'])

            if ('nextPageToken' not in result or result['nextPageToken'] is None): # No more pages
                return folders
            else: # There are more pages
                nextPageToken = result['nextPageToken']

        else: # No (more) folders found
            return folders



#
#   Helper method that checks if a project has a label set to a value
#
def checkIfProjectHasLabel(project, label, value):

    projectResource = cloudresourcemanager_get_project(project)
    return ( label in projectResource['labels'] and projectResource['labels'][label] == value )



#
# Returns a project resource object
# https://developers.google.com/resources/api-libraries/documentation/cloudresourcemanager/v1/python/latest/cloudresourcemanager_v1.projects.html#get
#
def cloudresourcemanager_get_project(projectId):
    return cloudresourcemanager_get_api_client().projects().get(projectId = projectId).execute()


#
# The projects.list() method specifies that there is a limit to the number of projects returned on each call
# A nextPageToken will be return in case the list has been truncated
#
def cloudresourcemanager_get_projects(requestedPageSize = 0, projectFilter = constants.PROJECT_FILTER, lifecycleState = "ACTIVE"):

    service = cloudresourcemanager_get_api_client()
    projects = []
    nextPageToken = None

    while True:
        # List Filter Examples can be found at:
        # https://developers.google.com/resources/api-libraries/documentation/cloudresourcemanager/v1/python/latest/cloudresourcemanager_v1.projects.html#list
        result = service.projects().list(filter = projectFilter, pageSize=requestedPageSize, pageToken=nextPageToken).execute()

        if 'projects' in result:
            for currentProject in result['projects']:
                if (currentProject['lifecycleState'] == lifecycleState):
                    projects.append(currentProject)

            if ('nextPageToken' not in result or result['nextPageToken'] is None): # No more pages
                return projects
            else: # There are more pages
                nextPageToken = result['nextPageToken']

        else: # No (more) projects found
            return projects


#
#   Returns IDs of projects accesible by the user tht match a given Name filter ( Filtered string list)
#
def cloudresourcemanager_get_project_ids(requestedPageSize = 0, projectFilter = constants.PROJECT_FILTER, lifecycleState = "ACTIVE"):

    result = []
    projects = cloudresourcemanager_get_projects( requestedPageSize = requestedPageSize, projectFilter = projectFilter, lifecycleState = lifecycleState)
    for project in projects:
        result.append(project['projectId'])

    return result


#
#   Returns IDs of projects which have been requested for deletion
#
def cloudresourcemanager_get_project_ids_deletion_requested (requestedPageSize = 0, projectFilter = constants.PROJECT_FILTER):
    return cloudresourcemanager_get_project_ids(requestedPageSize, projectFilter, lifecycleState = "DELETE_REQUESTED")



#
#   Returns all ACTIVE projects accesible by the user (Unfiltered DICT list)
#
def cloudresourcemanager_get_all_projects(requestedPageSize = 0):
    return cloudresourcemanager_get_projects(requestedPageSize = requestedPageSize)


#
#   Returns IDs of all ACTIVE projects accesible by the user (Unfiltered string list)
#
def cloudresourcemanager_get_all_project_ids(requestedPageSize = 0):
    return cloudresourcemanager_get_project_ids(requestedPageSize = requestedPageSize)


#
# Prints data of all projects readable by the user
#
def cloudresourcemanager_print_all_projects(requestedPageSize = 0):
    projects = cloudresourcemanager_get_all_projects(requestedPageSize)
    if not projects:
        print('[FATAL] No Projects Found.')
    else:
        for project in projects:
            labels = json.dumps(project.get('labels', ''), sort_keys=True)
            print('{0}|{1}|{2}|{3}|{4}'.format(project['projectNumber'],
                                               project['projectId'],
                                               project['name'],
                                               project['lifecycleState'],
                                               labels))
        print('\n\n[INFO] Total: {0} projects found.\n\n'.format(len(projects), requestedPageSize))

#
# Prints the all projects and a specific label
#

def cloudresourcemanager_print_project_and_label_value(requestedPageSize = 0, requested_label = 'budget_owner'):
    projects = cloudresourcemanager_get_all_projects(requestedPageSize)
    if not projects:
        print('[FATAL] No Projects Found.')
    else:
        for project in projects:
            labels = json.dumps(project.get('labels', ''), sort_keys=True)
            filtered_label = search_labels(labels, requested_label)

            label = search_labels(labels,requested_label)

            print('{0}|{1}'.format(project['projectId'],
                                   label))
            # what to do if label not found?
        print('\n\n[INFO] Total: {0} projects found.\n\n'.format(len(projects), requestedPageSize))


#
# Search labels
#

def search_labels(labels,requested_label):
    filtered_result = '';
    label_json = json.loads(labels)

    if requested_label.lower() in label_json:
      filtered_result = label_json[requested_label]

    return filtered_result



###########################################################
#
# Project IAM Policies and Bindings
#
###########################################################

#
# Returns a list of IamPolicy objects
# https://developers.google.com/resources/api-libraries/documentation/cloudresourcemanager/v1/python/latest/cloudresourcemanager_v1.projects.html#getIamPolicy
#
def cloudresourcemanager_get_all_projects_iam_policies():

    iamPolicies = []

    for projectId in cloudresourcemanager_get_all_project_ids():
        iamPolicies.append( cloudresourcemanager_get_project_iam_policy(projectId) )

    return iamPolicies



#
# Returns an iamPolicy object for a project
# https://developers.google.com/resources/api-libraries/documentation/cloudresourcemanager/v1/python/latest/cloudresourcemanager_v1.projects.html#getIamPolicy
#
def cloudresourcemanager_get_project_iam_policy(projectId):
    return cloudresourcemanager_get_api_client().projects().getIamPolicy(resource=projectId, body={}).execute()


#
# Sets the iamPolicy object for a project
# https://developers.google.com/resources/api-libraries/documentation/cloudresourcemanager/v1/python/latest/cloudresourcemanager_v1.projects.html#getIamPolicy
#
def cloudresourcemanager_set_project_iam_policy(projectId, policy):
    policy_body = "{{ \"policy\": {0} }}".format(json.dumps(policy))
    return cloudresourcemanager_get_api_client().projects().setIamPolicy(resource=projectId, body=json.loads(policy_body)).execute()


#
# Returns the iamBindings list for a project
# https://developers.google.com/resources/api-libraries/documentation/cloudresourcemanager/v1/python/latest/cloudresourcemanager_v1.projects.html#getIamPolicy
#
def cloudresourcemanager_get_project_iam_bindings(projectId):
    iamPolicy = cloudresourcemanager_get_project_iam_policy(projectId)
    if 'bindings' in iamPolicy:
        return iamPolicy['bindings']
    else:
        return None # Possibly lack of permissions


#
# Returns a list of iamBindings lists for each project
# https://developers.google.com/resources/api-libraries/documentation/cloudresourcemanager/v1/python/latest/cloudresourcemanager_v1.projects.html#getIamPolicy
#
def cloudresourcemanager_get_all_projects_iam_bindings():

    iamBindings = []

    for projectId in cloudresourcemanager_get_all_project_ids():
        bindings = cloudresourcemanager_get_project_iam_bindings(projectId)
        if bindings is not None:
            iamBindings.append(bindings)

    return iamBindings


#
# Returns the Binding for a specific role on a given project
#
def cloudresourcemanager_get_project_binding( projectId, role ):

    service = cloudresourcemanager_get_api_client()
    request = service.projects().getIamPolicy(resource=projectId, body={}).execute()
    bindings = request['bindings']
    for binding in bindings:
        if binding is not None and binding['role'] == role:
            return binding

#
# Returns all members of a binding for a given project
#
def cloudresourcemanager_get_project_binding_members(projectId, role):
    binding = cloudresourcemanager_get_project_binding(projectId, role)
    members = []
    if binding is not None:
        for member in binding['members']:
            members.append(member)
    return members


#
#
#
def cloudresourcemanager_get_project_owners(projectId):
    return cloudresourcemanager_get_project_binding_members(projectId, 'roles/owner')


#
#
#
def cloudresourcemanager_print_project_owners( projectId ):
    owners = cloudresourcemanager_get_project_owners(projectId)
    print('PROJECT {0} OWNERS'.format(projectId))
    for member in owners:
        print('{0}'.format(member))

#
#
#
def cloudresourcemanager_remove_member_from_project_binding ( projectId, role, memberToRemove ):

    policy = cloudresourcemanager_get_project_iam_policy(projectId)
    if policy is None:
        raise Exception("The IAM policy for project {0} could not be retrieved".format(projectId))

    i = 0
    for binding in policy['bindings']:
        #print("[DEBUG] Binding Role {0}".format(binding['role']))
        #print("[DEBUG] MEMBERS: {0}".format(json.dumps(binding['members'])))
        if binding['role'] == role:
            try:

                policy['bindings'][i]['members'].remove(memberToRemove)
                print("[INFO] Member {0} removed from {1} role binding".format(memberToRemove, role))
                #print("[DEBUG] New Binding: {0}".format(json.dumps(binding['members'])))

                # setIAMPolicy to update the policy for the project
                newPolicy = cloudresourcemanager_set_project_iam_policy( projectId, policy )
                print("[INFO] Success - Member {0} was removed successfully from role binding. New member list is: {1}".format(memberToRemove, json.dumps(policy['bindings'][i]['members'])))

            except Exception as exc:
                print("[INFO] Exception caught: {0}".format(exc))
                print("[INFO] Member {0} could not be found or could not be removed from {1} role binding.".format(memberToRemove, role))

        i += 1




#
#
#
def cloudresourcemanager_add_member_to_project_binding ( projectId, role, memberToAdd ):

    policy = cloudresourcemanager_get_project_iam_policy(projectId)
    if policy is None:
        raise Exception("The IAM policy for project {0} could not be retrieved".format(projectId))

    i = 0
    for binding in policy['bindings']:
        #print("[DEBUG] Binding Role {0}".format(binding['role']))
        #print("[DEBUG] MEMBERS: {0}".format(json.dumps(binding['members'])))
        if binding['role'] == role:
            try:
                policy['bindings'][i]['members'].append(memberToAdd)
                print("[INFO] Member {0} added to {1} role binding".format(memberToAdd, role))
                #print("[DEBUG] New Binding: {0}".format(json.dumps(binding['members'])))

                # setIAMPolicy to update the policy for the project
                newPolicy = cloudresourcemanager_set_project_iam_policy( projectId, policy )
                print("[INFO] Success - Member {0} was added successfully to role binding. New member list is: {1}".format(memberToAdd, json.dumps(policy['bindings'][i]['members'])))

            except Exception as exc:
                print("[WARNING] Exception caught: {0}".format(exc))
                print("[WARNING] Member {0} could not be added to binding for {1} role binding. Check if it exists already".format(memberToAdd, role))

        i += 1


###########################################################
#
# Project Organisation Policies
#
###########################################################

#
# Returns an orgPolicy object for a project
# https://developers.google.com/resources/api-libraries/documentation/cloudresourcemanager/v1/python/latest/cloudresourcemanager_v1.projects.html#listAvailableOrgPolicyConstraints
# https://developers.google.com/resources/api-libraries/documentation/cloudresourcemanager/v1/python/latest/cloudresourcemanager_v1.projects.html#getEffectiveOrgPolicy
#
# This process is extremely slow - It takes several seconds to retrieve the information for each project
#
def cloudresourcemanager_get_project_organisation_policy(projectId):

    resourcePath = "projects/{0}".format(projectId)

    availablePolicyConstraints = cloudresourcemanager_get_api_client().projects().listAvailableOrgPolicyConstraints(resource=resourcePath, body={}).execute()
    policy = []

    if "constraints" in availablePolicyConstraints:

        for constraint in availablePolicyConstraints["constraints"]:

            body = '''{{ "constraint": "{0}" }}'''.format(constraint["name"])
            policyForConstraint = cloudresourcemanager_get_api_client().projects().getEffectiveOrgPolicy(resource=resourcePath, body=json.loads(body)).execute()
            policy.append(policyForConstraint)

        return policy

    else:
        return {}


#
# Returns a list of effective orgPolicy objects
# https://developers.google.com/resources/api-libraries/documentation/cloudresourcemanager/v1/python/latest/cloudresourcemanager_v1.projects.html#getEffectiveOrgPolicy
#
def cloudresourcemanager_get_all_projects_organisation_policies():

    orgPolicies = []

    for projectId in cloudresourcemanager_get_all_project_ids():
        orgPolicies.append( cloudresourcemanager_get_project_organisation_policy(projectId) )

    return orgPolicies
