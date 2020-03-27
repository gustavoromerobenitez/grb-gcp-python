#!/usr/bin/python
import sys
import googleapiclient.discovery as discovery
import google_directory_utils as directory_utils

SECRETS_API_CLIENT = None
SECRETS_API_CLIENT_VERSION = None

# [START secrets_get_api_client]
def secrets_get_api_client(version = "v1beta1"):
    global SECRETS_API_CLIENT
    global SECRETS_API_CLIENT_VERSION
    if SECRETS_API_CLIENT == None or SECRETS_API_CLIENT_VERSION != version:
        SECRETS_API_CLIENT = discovery.build('secretmanager', version)
        SECRETS_API_CLIENT_VERSION = version
    return SECRETS_API_CLIENT
# [END secrets_get_api_client]

################################################################################
#
#   GOOGLE SECRETS COMMON FUNCTIONS
#
#   This library has just been started as an example
#   of how to interact with the Secret Manager API
#
###############################################################################

# https://cloud.google.com/secret-manager/docs/accessing-the-api

def get_secret(project_id, secret_id):
    """
    Get information about the given secret. This only returns metadata about
    the secret container, not any secret material.
    """

    # Get the secret
    response = secrets_get_api_client().projects().secrets().get( "projects/{0}/secrets/{1}".format( project_id, secret_id ) )

    # Get the replication policy.
    if response.replication.automatic:
        replication = 'AUTOMATIC'
    elif response.replication.user_managed:
        replication = 'MANAGED'
    else:
        raise 'Unknown replication {}'.format(response.replication)

    # Print data about the secret.
    print('Got secret {} with replication policy {}'.format( response.name, replication))

def access_secret_version(project_id, secret_id, version_id = 'latest'):
    """
    Access the payload for the given secret version if one exists. The version
    can be a version number as a string (e.g. "5") or an alias (e.g. "latest").
    """

    # Access the secret version.
    response = secrets_get_api_client().projects().secrets().versions().access( name = "projects/{0}/secrets/{1}/versions/{2}".format( project_id, secret_id, version_id ) ).execute()

    # Return the secret payload.
    #
    # WARNING: Do not print the secret in a production environment - this
    # snippet is showing how to access the secret material.
    payload = response['payload']['data'].decode('base64')
    #print('Plaintext: {}'.format(payload))
    return(format(payload))
