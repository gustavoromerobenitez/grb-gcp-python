#!/usr/bin/python
import sys
import re
import argparse
import json
import datetime as dt
import googleapiclient.discovery
import google_constants as constants
import google_compute_utils as computeUtils
import google_cloudresourcemanager_utils as resourceManagerUtils
import google_dataproc_utils as dataprocUtils
from googleapiclient.errors import HttpError



def calculateDeletionDate(deletionGracePeriod):

    if deletionGracePeriod == constants.GRACE_PERIOD_ONE_WEEK:
        deletionDate = "{0}".format( (dt.datetime.now() +  dt.timedelta(days=7)).strftime('%Y%m%d') )
    else:
        if deletionGracePeriod == constants.GRACE_PERIOD_ONE_MONTH:
            deletionDate = "{0}".format( (dt.datetime.now() +  dt.timedelta(days=30)).strftime('%Y%m%d') )
        else: # Set the deletion date to a year from now if it does not match any known policy
            deletionDate = "{0}".format( (dt.datetime.now() +  dt.timedelta(days=365)).strftime('%Y%m%d') )

    return deletionDate


#################################################################
#
#   Scans through all the Disks in the project
# and determines whether they should be marked for deletion
#
def markDisksForDeletion(project, zone):

    disks = computeUtils.compute_list_disks(project, zone)

    print "\n\n[INFO] =============================="
    print "[INFO] # of Disks: {0}".format(len(disks))
    print "[INFO] =============================="

    for disk in disks:

        markForDeletionDecision =  False
        deletionGracePeriod = constants.GRACE_PERIOD_NOT_SET
        inService = False
        inUseBy = ""

        markedForDeletion = False
        markedForDeletionValue = "NO"

        if "labels" in disk:
            if constants.MARKED_FOR_DELETION_LABEL in disk["labels"] :
                markedForDeletion = True
                markedForDeletionValue = disk["labels"][constants.MARKED_FOR_DELETION_LABEL]

            if constants.GRACE_PERIOD_LABEL in disk['labels'] :
                deletionGracePeriod = disk['labels'][constants.GRACE_PERIOD_LABEL]

        # Mark for deletion
        # if the disk is not in use by any VM
        # and a Grace Period has been set
        # and the disk has been detached for longer than the specified time in the policy
        markForDeletionDecision = ( not markedForDeletion
                    and ( "users" not in disk or ( "users" in disk and disk['users'] == "") )
                    and deletionGracePeriod != constants.GRACE_PERIOD_NOT_SET
                    and deletionGracePeriod != constants.DO_NOT_DELETE_VALUE )

        print '\n[INFO] Disk {0} - Marked for Deletion: {1} - Date: {2}'.format(disk['name'], markedForDeletion, markedForDeletionValue)

        if "users" in disk:
            print '[INFO] Disk {0} - In Use By: {1}'.format(disk['name'], disk['users'])
        else:
            print '[INFO] Disk {0} - NOT IN USE'.format(disk['name'])


        if "lastAttachTimestamp" in disk:
            print '[INFO] Disk {0} - LastAttachTimestamp: {1}'.format(disk['name'], disk['lastAttachTimestamp'])
        else:
            print '[INFO] Disk {0} - No LastAttachTimestamp'.format(disk['name'])


        if "lastDetachTimestamp" in disk:
            print '[INFO] Disk {0} - LastDetachTimestamp: {1}'.format(disk['name'], disk['lastDetachTimestamp'])
        else:
            print '[INFO] Disk {0} - No LastDetachTimestamp'.format(disk['name'])


        print '[INFO] Disk {0} - Grace Period: {1}'.format(disk['name'], deletionGracePeriod)
        print '[INFO] Disk {0} - Mark For Deletion Decision: {1}'.format(disk['name'], markForDeletionDecision)

        if markForDeletionDecision :

            # Calculate the deletion date based on the value of the Grace Period Tag
            deletionDate = calculateDeletionDate(deletionGracePeriod)

            disk["labels"][ constants.MARKED_FOR_DELETION_LABEL ] = str( constants.MARKED_FOR_DELETION_VALUE_PREFIX + deletionDate )
            newLabelBody = { "labels": disk["labels"], "labelFingerprint": disk["labelFingerprint"] } # This will overwrite all tags as it uses the same fingerprint
            operation = computeUtils.compute_set_disk_label(project, zone, disk['name'], newLabelBody)
            computeUtils.compute_wait_for_operation(project, zone, operation['name'])

            print constants.MARKED_FOR_DELETION_MESSAGE.format(project, "Compute Disk", disk['name'], deletionDate)





######################################################################
#
#   Scans through all the VMs in the project
# and determines whether they should be marked for deletion
#
def markInstancesForDeletion(project, zone):

    instances = computeUtils.compute_list_instances(project, zone)

    print "\n\n[INFO] =============================="
    print "[INFO] # of VMs: {0}".format(len(instances))
    print "[INFO] =============================="

    for instance in instances:

        markForDeletionDecision =  False
        deletionGracePeriod = constants.GRACE_PERIOD_NOT_SET
        deletionProtectionEnabled = False

        markedForDeletion = False
        markedForDeletionValue = "NO"

        if "labels" in instance:
            if constants.MARKED_FOR_DELETION_LABEL in instance["labels"] :
                markedForDeletion = True
                markedForDeletionValue = instance["labels"][constants.MARKED_FOR_DELETION_LABEL]

            if constants.GRACE_PERIOD_LABEL in instance['labels'] :
                deletionGracePeriod = instance['labels'][constants.GRACE_PERIOD_LABEL]


        if "deletionProtection" in instance :
            deletionProtectionEnabled = instance['deletionProtection']

        # Mark for deletion
        # if the VM is terminated
        # and a Grace Period has been set
        # and the VM is not protected against deletion
        # TODO ----  and the policy matches the time the VM has been stopped
        # The instance status can be one of the following values: PROVISIONING, STAGING, RUNNING, STOPPING, STOPPED, SUSPENDING, SUSPENDED, and TERMINATED.
        markForDeletionDecision = ( not markedForDeletion
                    and instance['status'] == "TERMINATED"
                    and not deletionProtectionEnabled
                    and deletionGracePeriod != constants.GRACE_PERIOD_NOT_SET
                    and deletionGracePeriod != constants.DO_NOT_DELETE_VALUE )


        print '\n[INFO] Instance {0} - Status: {1}'.format(instance['name'], instance['status'])
        print '[INFO] Instance {0} - Is Already Marked for Deletion?: {1} - Date: {2}'.format(instance['name'], markedForDeletion, markedForDeletionValue)
        print '[INFO] Instance {0} - Deletion Protection: {1}'.format(instance['name'], deletionProtectionEnabled)
        print '[INFO] Instance {0} - Grace Period: {1}'.format(instance['name'], deletionGracePeriod)
        print '[INFO] Instance {0} - Mark For Deletion Decision: {1}'.format(instance['name'], markForDeletionDecision)

        if markForDeletionDecision:

            # Calculate the deletion date based on the value of the Grace Period Tag
            deletionDate = calculateDeletionDate(deletionGracePeriod)

            instance["labels"][ constants.MARKED_FOR_DELETION_LABEL ] = str( constants.MARKED_FOR_DELETION_VALUE_PREFIX + deletionDate )
            newLabelBody = { "labels": instance["labels"], "labelFingerprint": instance["labelFingerprint"] }
            operation = computeUtils.compute_set_instance_label(project, zone, instance['name'], newLabelBody)
            computeUtils.compute_wait_for_operation(project, zone, operation['name'])

            print constants.MARKED_FOR_DELETION_MESSAGE.format(project, "Compute Instance", instance['name'], deletionDate)




#########################################################################
#
#   Scans through all the Dataproc Clusters in the project
# and determines whether they should be marked for deletion
#
def markDataprocClustersForDeletion(project, region, zone):

    clusters = dataprocUtils.dataproc_list_clusters(project, region)

    print "\n\n[INFO] =============================="
    print "[INFO] # of Dataproc Clusters: {0}".format(len(clusters))
    print "[INFO] =============================="

    for cluster in clusters:

        markForDeletionDecision =  False
        deletionGracePeriod = constants.GRACE_PERIOD_NOT_SET
        deletionProtectionEnabled = False

        markedForDeletion = False
        markedForDeletionValue = "NO"

        if "labels" in cluster:
            if constants.MARKED_FOR_DELETION_LABEL in cluster["labels"] :
                markedForDeletion = True
                markedForDeletionValue = cluster["labels"][constants.MARKED_FOR_DELETION_LABEL]

            if constants.GRACE_PERIOD_LABEL in cluster["labels"] :
                deletionGracePeriod = cluster["labels"][constants.GRACE_PERIOD_LABEL]


        # Mark for deletion
        # The cluster status.state can be one of the following: ACTIVE, INACTIVE, CREATING, RUNNING, ERROR, DELETING, or UPDATING.
        #
        # ACTIVE contains the CREATING, UPDATING, and RUNNING states.
        # INACTIVE contains the DELETING and ERROR statesself.
        #
        # Even when all the VMs in the cluster are stopped, the cluster is still marked as ACTIVE !
        #
        markForDeletionDecision = ( not markedForDeletion
                    and deletionGracePeriod != constants.GRACE_PERIOD_NOT_SET
                    and deletionGracePeriod != constants.DO_NOT_DELETE_VALUE )


        print '\n[INFO] Dataproc Cluster {0} - Status.State: {1}'.format(cluster["name"], cluster["state"])
        print '[INFO] Dataproc Cluster {0} - Is Already Marked for Deletion? : {1} - Date: {2}'.format(cluster["name"], markedForDeletion, markedForDeletionValue)
        print '[INFO] Dataproc Cluster {0} - Grace Period: {1}'.format(cluster["name"], deletionGracePeriod)
        print '[INFO] Dataproc Cluster {0} - Mark For Deletion Decision: {1}'.format(cluster["name"], markForDeletionDecision)

        if markForDeletionDecision:

            # Calculate the deletion date based on the value of the Grace Period Tag
            deletionDate = calculateDeletionDate(deletionGracePeriod)

            cluster["labels"][ constants.MARKED_FOR_DELETION_LABEL ] = str( constants.MARKED_FOR_DELETION_VALUE_PREFIX + deletionDate )
            dataprocUtils.dataproc_set_cluster_labels(project, region, cluster["name"], cluster["labels"])

            print constants.MARKED_FOR_DELETION_MESSAGE.format(project, "Dataproc Cluster", cluster["name"], deletionDate)



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


        markInstancesForDeletion(project, zone)
        markDisksForDeletion(project, zone)
        markDataprocClustersForDeletion(project, region, zone)
        # ...etc




if __name__ == '__main__':
    parser = argparse.ArgumentParser( description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-p','--projects', required=True, metavar='project', nargs='+', help='List of Google Cloud projects where the actions will be performed. Use "-p all" to affect all "managed" projects, i.e.: Projects with a label called '+constants.MANAGED_RESOURCE_DELETION_LABEL+' set to true) .')
    parser.add_argument('-z','--zone', default='europe-west1-b', help='Optional Compute Engine zone where the actions will be performed.')
    parser.add_argument('-r','--region', default='europe-west1', help='Optional Compute Engine Region where the actions will be performed.')
    args = parser.parse_args()
    main(args.projects, args.region, args.zone)
# [END run]
