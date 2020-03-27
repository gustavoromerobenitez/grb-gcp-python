#!/usr/bin/python
import sys
import re
import argparse
import time
import json
import googleapiclient.discovery

# The libraries are located one level above the scripts folder
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)

import google_constants as constants
import google_compute_utils as computeUtils
import google_cloudresourcemanager_utils as cloudResourceManagerUtils
from googleapiclient.errors import HttpError


# [START run]
def main(projectsArgumentList, requestedShutdownSchedule, zone):

    print "\n\n[INFO] ======================================================================================"

    if "all" in projectsArgumentList:
        projectList = cloudResourceManagerUtils.cloudresourcemanager_get_project_ids(projectFilter = constants.MANAGED_INSTANCE_SHUTDOWN_PROJECT_FILTER)
        print "[INFO] Projects where Compute Instance shutdown management is ENABLED (via {0}):\n[INFO] {1}".format(constants.MANAGED_INSTANCE_SHUTDOWN_LABEL, projectList)
    else:
        projectList = projectsArgumentList
        print "[INFO] Projects provided: {0}".format(projectList)

    print "[INFO] ======================================================================================"

    for project in projectList:

        print "\n\n[INFO] ======================================================================================"
        print "[INFO] Project: {0}".format(project)
        print "[INFO] Zone: {0}".format(zone)

        instances = []
        try:

            # Double check that these projects have the label labels.managed-vm-shutdown:true
            if not cloudResourceManagerUtils.checkIfProjectHasLabel(project, constants.MANAGED_INSTANCE_SHUTDOWN_LABEL, constants.MANAGED_INSTANCE_SHUTDOWN_DEFAULT_VALUE) :
                print "[ERROR] **********  COMPUTE INSTANCE SHUTDOWN MANAGEMENT NOT ENABLED  **************"
                print "[INFO] ======================================================================================"
                continue

            instances = computeUtils.compute_list_instances(project, zone)
            print "[INFO] # of Compute Instances: {0}".format(len(instances))
            print "[INFO] ======================================================================================"

        except HttpError as e:
            print "[ERROR] **********  PROJECT NOT FOUND  **************"
            print "[INFO] ======================================================================================"
            continue


        for instance in instances:

            shutdownDecision =  False
            shutdownSchedule = constants.SHUTDOWN_SCHEDULE_NOT_SET

            # Check the status of the instance.
            # It can be one of the following values:
            # PROVISIONING, STAGING, RUNNING, STOPPING, STOPPED, SUSPENDING, SUSPENDED, and TERMINATED.
            instanceResource = computeUtils.compute_get_instance(project, zone, instance['name'])

            if "labels" in instanceResource and constants.SHUT_DOWN_SCHEDULE_LABEL in instanceResource['labels']:
                shutdownSchedule = instanceResource['labels'][constants.SHUT_DOWN_SCHEDULE_LABEL]

            # Shut down only if a schedule has been set and the schedule allows the VM to be shutdown
            shutdownDecision = ( instanceResource['status'] == "RUNNING"
                        and shutdownSchedule != constants.SHUTDOWN_SCHEDULE_NOT_SET
                        and shutdownSchedule != constants.DO_NOT_SHUTDOWN_VALUE
                        and shutdownSchedule == requestedShutdownSchedule)


            print '\n[INFO] Instance {0} - Status: {1}'.format(instance['name'], instanceResource['status'])
            print '[INFO] Instance {0} - Shutdown Schedule: {1}'.format(instance['name'], shutdownSchedule)
            print '[INFO] Instance {0} - Shutdown Decision: {1}'.format(instance['name'], shutdownDecision)

            if shutdownDecision:

                print '[INFO] Instance {0} - Stopping instance'.format(instance['name']),#The comma avoids a new line after the print
                operation = computeUtils.compute_stop_instance(project, zone, instance['name'])
                computeUtils.compute_wait_for_operation(project, zone, operation['name'])

                instanceResource = computeUtils.compute_get_instance(project, zone, instance['name'])
                print '[INFO] Instance {0} - Status: {1}\n'.format(instance['name'], instanceResource['status'])



if __name__ == '__main__':
    parser = argparse.ArgumentParser( description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-s','--schedule', required='True', choices=['daily', 'weekly', 'monthly'])
    parser.add_argument('-p','--projects', required=True, metavar='project', nargs='+', help='List of one or more Google Cloud projects where the actions will be performed.\nUse "-p all" to affect all "managed" projects, i.e.: Projects with a label called '+constants.MANAGED_INSTANCE_SHUTDOWN_LABEL+' set to true) .')
    parser.add_argument('-z','--zone', default='europe-west1-b', help='Optional Compute Engine zone where the actions will be performed.')
    args = parser.parse_args()
    main(args.projects, args.schedule, args.zone)
# [END run]
