#!/usr/bin/python
import sys
import re
import argparse
import json
import datetime as dt
import googleapiclient.discovery

# The libraries are located one level above the scripts folder
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)

import google_constants as constants
import google_compute_utils as computeUtils
import google_cloudresourcemanager_utils as resourceManagerUtils
import google_dataproc_utils as dataprocUtils
from googleapiclient.errors import HttpError


###########################################################################
#
# Checks which resources have been marked for deletion and are past their grace
# period end date
#
def checkIfResourcesArePastGracePeriod(resourceList, resourceType):

    print "\n\n[DEBUG] =============================="
    print "[DEBUG] # of {0}s: {1}".format(resourceType, len(resourceList))
    print "[DEBUG] =============================="

    for resource in resourceList:

        if "labels" not in resource or constants.MARKED_FOR_DELETION_LABEL not in resource["labels"] :
            print "[DEBUG] {0} {1} - Not Marked for Deletion.".format(resourceType, resource['name'])
            continue

        markedForDeletionValue = resource["labels"][constants.MARKED_FOR_DELETION_LABEL]
        gracePeriodEndString = re.match("{0}(\\d+)".format(constants.MARKED_FOR_DELETION_VALUE_PREFIX), markedForDeletionValue).group(1)
        gracePeriodEndDate = dt.datetime.strptime(gracePeriodEndString, "%Y%m%d")

        if gracePeriodEndDate > dt.datetime.now() :
            print "[DEBUG] {0} {1} - Marked for Deletion {2} but still within its grace period.".format(resourceType, resource['name'], markedForDeletionValue)
            continue

        print "[INFO] {0} {1} - was marked for deletion {2} and is now past its grace period and CAN BE DELETED".format(resourceType, resource['name'], markedForDeletionValue)



# [START run]
def main(projectsArgumentList, region, zone):

    print "\n\n[INFO] ======================================================================================"

    if "all" in projectsArgumentList:
        projectList = resourceManagerUtils.cloudresourcemanager_get_project_ids(projectFilter = constants.MANAGED_RESOURCE_DELETION_PROJECT_FILTER)
        print "[INFO] Projects where resource deletion management is ENABLED (via label {0}):\n[INFO] {1}".format(constants.MANAGED_RESOURCE_DELETION_LABEL, projectList)
    else:
        projectList = projectsArgumentList
        print "[INFO] Projects provided: {0}".format(projectList)

    print "[INFO] ======================================================================================"

    for project in projectList:

        print "\n\n[INFO] ======================================================================================"
        print "[INFO] Project: {0}".format(project)
        print "[INFO] Zone: {0}".format(zone)

        try:
            # Double check that these projects have the label labels.managed-resource-deletion:true
            if not resourceManagerUtils.checkIfProjectHasLabel(project, constants.MANAGED_RESOURCE_DELETION_LABEL, constants.MANAGED_RESOURCE_DELETION_VALUE) :
                print "[ERROR] **********  RESOURCE DELETION MANAGEMENT NOT ENABLED  **************"
                print "[INFO] ======================================================================================"
                continue

        except HttpError as e:
            print "[ERROR] **********  PROJECT NOT FOUND  **************"
            print "[INFO] ======================================================================================"
            continue

        print "[INFO] ======================================================================================"


        disks = computeUtils.compute_list_disks(project, zone)
        checkIfResourcesArePastGracePeriod(disks, "DISK")

        instances = computeUtils.compute_list_instances(project, zone)
        checkIfResourcesArePastGracePeriod(instances, "INSTANCE")

        dataprocClusters = dataprocUtils.dataproc_list_clusters(project, region)
        checkIfResourcesArePastGracePeriod(dataprocClusters, "DATAPROC CLUSTER")

        # ...etc




if __name__ == '__main__':
    parser = argparse.ArgumentParser( description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-p','--projects', required=True, metavar='project', nargs='+', help='List of Google Cloud projects where the actions will be performed. Use "-p all" to affect all "managed" projects, i.e.: Projects with a label called '+constants.MANAGED_RESOURCE_DELETION_LABEL+' set to true) .')
    parser.add_argument('-z','--zone', default='europe-west1-b', help='Optional Compute Engine zone where the actions will be performed.')
    parser.add_argument('-r','--region', default='europe-west1', help='Optional Compute Engine Region where the actions will be performed.')
    args = parser.parse_args()
    main(args.projects, args.region, args.zone)
# [END run]
