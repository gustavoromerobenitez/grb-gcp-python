#!/usr/bin/python
import os
import sys
import re
import argparse
import time
import datetime as dt
import googleapiclient.discovery
import google_constants as constants
import google_cloudsql_utils as cloudSQLUtils
import google_cloudresourcemanager_utils as cloudResourceManagerUtils
from googleapiclient.errors import HttpError
from subprocess import check_output, PIPE, STDOUT



# globalVars
globalVars = {}
globalVars["REPORT"] = []
globalVars["REPORT_BASE_FILENAME"] = "sql-instances-audit-report"
globalVars["REPORT_FILE_EXTENSION"] = "csv"


def writeReport(date):
    reportFilename = "{0}_{1}.{2}".format(globalVars["REPORT_BASE_FILENAME"], date, globalVars["REPORT_FILE_EXTENSION"])
    print "\n\n[INFO] Writing report to file {0}".format(reportFilename)

    with open(reportFilename, 'w') as f:
        f.write("PROJECT\tSQL_INSTANCE\tSSL_REQUIRED\n")
        for line in globalVars["REPORT"]:
            f.write("{0}\n".format(line))



def report(project, instanceName, requireSSL):
    outputString = "{0}\t{1}\t{2}".format(project, instanceName, requireSSL)
    globalVars["REPORT"].append(outputString)
    print "[INFO] [REPORT] {0}".format(outputString)




# [START run]
def main(projectsArgumentList):

    print "\n\n[INFO] ======================================================================================"

    if "all" in projectsArgumentList:
        projectList = cloudResourceManagerUtils.cloudresourcemanager_get_project_ids()
    else:
        projectList = projectsArgumentList

    print "\n\n[INFO] Starting CloudSQL Instance Security Audit Report for {0} GCP Projects :".format(len(projectList))
    for p in projectList:
        print "[INFO] {0}".format(p)

    print "[INFO] ======================================================================================"

    for project in projectList:

        print "\n\n[INFO] ======================================================================================"
        print "[INFO] Project: {0}".format(project)

        instances = []
        try:

            instances = cloudSQLUtils.cloudsql_list_instances(project)
            print "[INFO] # CloudSQL Instances: {0}".format(len(instances))
            print "[INFO] ======================================================================================"

        except HttpError as e:
            print "[INFO] ======================================================================================"
            report(project, "N/A", "N/A")
            continue


        for instance in instances:
            requireSSL = "SSL_NOT_REQUIRED"
            if ( "settings" in instance
                  and "ipConfiguration" in instance['settings']
                  and "requireSsl" in instance['settings']['ipConfiguration']
                  and instance['settings']['ipConfiguration']['requireSsl'] ):
                requireSSL = "SSL_REQUIRED"

            report(project, instance['name'], requireSSL)


    # Write the report to file
    dateString = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    writeReport(dateString)


if __name__ == '__main__':
    parser = argparse.ArgumentParser( description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-p','--projects', required=True, metavar='project', nargs='+', help='List of one or more Google Cloud projects where the actions will be performed.\nUse "-p all" to affect all projects.')
    args = parser.parse_args()
    main(args.projects)
# [END run]
