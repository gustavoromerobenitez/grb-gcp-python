#!/usr/bin/python
import sys
import re
import time
import inspect
from google.cloud import dataproc_v1
from google.cloud.dataproc_v1.gapic.transports import cluster_controller_grpc_transport



################################################################################
#
#   GOOGLE CLOUD DATAPROC COMMON FUNCTIONS
#
#   The Dataproc Python libraries are in Alpha as of 2019-02
#
#   Alternatively there is REST API available to interact with Cloud Dataproc
#
#   https://dataproc.googleapis.com
#   https://cloud.google.com/dataproc/docs/reference/rest/
#
#
###############################################################################

#
# The objects of the CLuster Class cannot be converted into a dict using any of the usual methods (dict, vars, __dict__, etc)
# The resulting dict does not have the fields accessible cia the object attributes
#
# We only need the cluster_name (as name) and the labels, hence we create a custom dict
#
def clusterObjectToDict(clusterObj):

    dict = {}

    if clusterObj != None :
        dict['name'] = clusterObj.cluster_name
        dict['labels'] = clusterObj.labels
        dict['state'] = clusterObj.status.state

    return dict



#
# google.api_core.exceptions.InvalidArgument: 400 Region 'europe-west1' specified in request does not match endpoint region 'global'.
# To use 'europe-west1' region, specify 'europe-west1' region in request and configure client to use 'europe-west1-dataproc.googleapis.com:443' endpoint.
#
def dataproc_get_client(region):

    transport = cluster_controller_grpc_transport.ClusterControllerGrpcTransport(address="{0}-dataproc.googleapis.com:443".format(region))
    return dataproc_v1.ClusterControllerClient(transport)


#
#   https://googleapis.github.io/google-cloud-python/latest/dataproc/gapic/v1/api.html#google.cloud.dataproc_v1.ClusterControllerClient.list_clusters
#   Lists all regions/{region}/clusters in a project.
#
def dataproc_list_clusters(project, region):

    result = []
    clusterList = []

    try:
        clusterList = list(dataproc_get_client(region).list_clusters(project, region))
    except Exception as e:
        print "\n[WARN] {0}".format(e.message)
        return []

    for object in clusterList:
        result.append(clusterObjectToDict(object))

    return result



#
#
#
def dataproc_list_inactive_clusters(project, region):

    result = []
    clusterList = []

    try:
        clusterList = list(dataproc_get_client(region).list_clusters(project, region, filter_ = "status.state = INACTIVE"))
    except Exception as e:
        print "\n[WARN] {0}".format(e.message)
        return []

    for object in clusterList:
        result.append(clusterObjectToDict(object))

    return result



def dataproc_get_cluster(project, region, clusterName):

    cluster = None

    try:
        cluster = dataproc_get_client(region).get_cluster(project, region, clusterName)
    except Exception as e:
        print "\n[WARN] {0}".format(e.message)

    return clusterObjectToDict(cluster)


#
# Not used because the script finishes before the callback completes, but could be used to trigger actions
#
def dataproc_set_cluster_labels_callback(operation_future):
    print "[DEBUG] Dataproc Set Cluster Labels callback result: {0}".format(operation_future.result())
    return operation_future.result()


#
#   This function is better understood by looking at the REST API
#   https://cloud.google.com/dataproc/docs/reference/rest/v1/projects.regions.clusters/patch
#
def dataproc_set_cluster_labels(project, region, clusterName, labels):

    changes = { "labels": labels}
    update_mask = { "paths": ["labels"] }
    response = None
    try:
        response = dataproc_get_client(region).update_cluster(project, region, clusterName, changes, update_mask)
        response.add_done_callback(dataproc_set_cluster_labels_callback)
    except Exception as e:
        print "\n[ERROR] {0}".format(e.message)
        raise #Let the Exception flow up
