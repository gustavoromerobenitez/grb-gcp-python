#!/usr/bin/python
import sys
import re
import argparse
import time
import datetime as dt
import googleapiclient.discovery

# The libraries are located one level above the scripts folder
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)

import google_constants as constants
import google_compute_utils as computeUtils
import google_cloudresourcemanager_utils as cloudResourceManagerUtils
from googleapiclient.errors import HttpError
from subprocess import check_output, PIPE, STDOUT



# globalVars
globalVars = {}
globalVars["REPORT"] = []
globalVars["REPORT_BASE_FILENAME"] = "compute-instances-audit-report"
globalVars["REPORT_FILE_EXTENSION"] = "csv"


def writeReport(date):
    reportFilename = "{0}_{1}.{2}".format(globalVars["REPORT_BASE_FILENAME"], date, globalVars["REPORT_FILE_EXTENSION"])
    print "\n\n[INFO] Writing report to file {0}".format(reportFilename)

    with open(reportFilename, 'w') as f:
        f.write("PROJECT\tCOMPUTE_INSTANCE\tSERIAL_PORTS\tPROJECT_SSH_KEYS\tOS_LOGIN\tIP_FORWARDING\tSERVICE_ACCOUNT_API_ACCESS\n")
        for line in globalVars["REPORT"]:
            f.write("{0}\n".format(line))



def report(project, instanceName, serialPorts, projectWideSSHKeys, osLogin, ipForwarding, serviceAccountAPIAccess):
    outputString = "{0}\t{1}\t{2}\t{3}\t{4}\t{5}\t{6}".format(project, instanceName, serialPorts, projectWideSSHKeys, osLogin, ipForwarding, serviceAccountAPIAccess )
    globalVars["REPORT"].append(outputString)
    print "[INFO] [REPORT] {0}".format(outputString)


# [START run]
def main(projectsArgumentList, zone):

    print "\n\n[INFO] ======================================================================================"

    if "all" in projectsArgumentList:
        projectList = cloudResourceManagerUtils.cloudresourcemanager_get_project_ids()
    else:
        projectList = projectsArgumentList

    print "\n\n[INFO] Starting Compute Instance Security Audit Report for {0} GCP Projects :".format(len(projectList))
    for p in projectList:
        print "[INFO] {0}".format(p)

    print "[INFO] ======================================================================================"

    for project in projectList:

        print "\n\n[INFO] ======================================================================================"
        print "[INFO] Project: {0}".format(project)

        instances = []
        try:
            instances = computeUtils.compute_list_instances(project, zone)
            print "[INFO] # of VMs: {0}".format(len(instances))
            print "[INFO] ======================================================================================"

        except HttpError as e:
            print "[INFO] ======================================================================================"
            report(project, "N/A", "N/A", "N/A", "N/A", "N/A", "N/A")
            continue


        #
        # TODO: FIX THIS. This is the Project Metadata but enable-oslogin belongs to the Compute Metadata and the key is called commonInstanceMetadata
        #
        projectOsLogin = "PROJECT_OS_LOGIN_DISABLED"
        projectComputeResource = computeUtils.compute_get_project(project)
        if "commonInstanceMetadata" in projectComputeResource and "items" in projectComputeResource['commonInstanceMetadata']:
            for item in projectComputeResource['commonInstanceMetadata']['items']:
                if ( item['key'] == "enable-oslogin" and re.match(constants.TRUE_REGEX, item['value'])):
                    projectOsLogin = "PROJECT_OS_LOGIN_ENABLED"

        for instance in instances:

            serialPorts = "SERIAL_PORTS_DISABLED"
            projectWideSSHKeys = "PROJECT_SSH_KEYS_ALLOWED"
            ipForwarding = "IP_FORWARDING_DISABLED"
            serviceAccountAPIAccess = "LIMITED_SCOPES"
            osLogin = projectOsLogin

            if "metadata" in instance and "items" in instance['metadata']:
                for item in instance['metadata']['items']:

                    if ( item['key'] == "serial-port-enable" and re.match(constants.TRUE_REGEX, item['value']) ):
                        serialPorts = "SERIAL_PORTS_ENABLED"
                    elif ( item['key'] == "block-project-ssh-keys" and re.match(constants.TRUE_REGEX, item['value']) ):
                        projectWideSSHKeys = "PROJECT_SSH_KEYS_BLOCKED"
                    elif ( item['key'] == "enable-oslogin" and re.match(constants.TRUE_REGEX, item['value']) ):
                        osLogin = "VM_OS_LOGIN_ENABLED"


            # "Enabling OS Login on instances disables metadata-based SSH key configurations on those instances"
            # https://cloud.google.com/compute/docs/instances/managing-instance-access#enable_oslogin
            # Not clear if enabling oslogin at project level has the same effect, hence it is not considered in this condition
            if osLogin == "VM_OS_LOGIN_ENABLED":
                projectWideSSHKeys = osLogin

            # Boolean Value, not String like the one in Metadata
            if ( "canIpForward" in instance and instance["canIpForward"]):
                ipForwarding = "IP_FORWARDING_ENABLED"

            if "serviceAccounts" in instance:
                for serviceAccount in instance['serviceAccounts']:
                    if "https://www.googleapis.com/auth/cloud-platform" in serviceAccount['scopes']:
                        serviceAccountAPIAccess = "FULL_SCOPES"

            report(project, instance['name'], serialPorts, projectWideSSHKeys, osLogin, ipForwarding, serviceAccountAPIAccess)


    # Write the report to file
    dateString = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    writeReport(dateString)



if __name__ == '__main__':
    parser = argparse.ArgumentParser( description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-p','--projects', required=True, metavar='project', nargs='+', help='List of one or more Google Cloud projects where the actions will be performed.\nUse "-p all" to affect all projects.')
    parser.add_argument('-z','--zone', default='europe-west1-b', help='Optional Compute Engine zone where the actions will be performed.')
    args = parser.parse_args()
    main(args.projects, args.zone)
# [END run]
