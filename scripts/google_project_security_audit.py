#!/usr/bin/python
import re
import argparse
import datetime as dt

# The libraries are located one level above the scripts folder
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)

import google_constants as constants
import google_cloudresourcemanager_utils as cloudResourceManagerUtils




# globalVars
globalVars = {}
globalVars["REPORT"] = []
globalVars["REPORT_BASE_FILENAME"] = "projects-security-audit-report"
globalVars["REPORT_FILE_EXTENSION"] = "csv"
globalVars["SVC_ACC_ADMIN_VIOLATION"] = "SERVICE_ACCOUNT_ASSIGNED_ADMIN_ROLE"
globalVars["USER_WITH_SVC_ACC_ROLE_VIOLATION"] = "USER_ASSIGNED_SERVICE_ACCOUNT_ROLE"
globalVars["SVC_ACC_ROLES_REGEX"] = "^roles/iam\.serviceAccount"
globalVars["USER_ACCOUNT_REGEX"] = "^user:.*"
globalVars["ADMIN_ROLE_REGEX"] = "^roles/(owner|[\w\.]*[aA]dmin)"
globalVars["SVC_ACC_REGEX"] = "^serviceAccount:.*{0}.iam.gserviceaccount.com"



def writeReport(date):
    reportFilename = "{0}_{1}.{2}".format(globalVars["REPORT_BASE_FILENAME"], date, globalVars["REPORT_FILE_EXTENSION"])
    print("\n\n[INFO] Writing report to file {0}".format(reportFilename))

    with open(reportFilename, 'w') as f:
        f.write("PROJECT\tVIOLATION\tROLE\tACCOUNT\n")
        for line in globalVars["REPORT"]:
            f.write("{0}\n".format(line))



def report(project, violation, role, account):
    outputString = "{0}\t{1}\t{2}\t{3}".format(project, violation, role, account )
    globalVars["REPORT"].append(outputString)
    print("[INFO] [REPORT] {0}".format(outputString))


#
# Looks for a specific regex in each member of a binding and report a violation if found
#
def check_violations (projectId, binding, roleRegex, violation, accountTypeRegex ):

    if re.search(roleRegex, binding['role']):
        for member in binding['members']:
            if re.search(accountTypeRegex, member):
                report(projectId, violation, binding['role'], member)



# [START run]
def main(projectsArgumentList):

    if "all" in projectsArgumentList:
        projectList = cloudResourceManagerUtils.cloudresourcemanager_get_project_ids(projectFilter = constants.PROJECT_FILTER)
    else:
        projectList = projectsArgumentList

    print("\n\n[INFO] ======================================================================================")
    print("[INFO] Starting Project Security Audit Report for {0} GCP Projects :".format(len(projectList)))
    for p in projectList:
        print("[INFO] {0}".format(p))
    print("[INFO] ======================================================================================")

    for projectId in projectList:

        print("\n\n[INFO] ======================================================================================")
        print("[INFO] Project: {0}".format(projectId))

        iamBindings = cloudResourceManagerUtils.cloudresourcemanager_get_project_iam_bindings(projectId)

        if iamBindings is None:
            print("[ERROR] UNABLE TO RETRIEVE PROJECT IAM BINDINGS")
            print("[INFO] ======================================================================================")
        else:
            print("[INFO] ======================================================================================")
            for binding in iamBindings:

                # Check for USER accounts which have Service Account roles assigned
                check_violations (projectId, binding, globalVars["SVC_ACC_ROLES_REGEX"], globalVars["USER_WITH_SVC_ACC_ROLE_VIOLATION"], globalVars["USER_ACCOUNT_REGEX"] )

                # Check for Service Accounts with Admin roles assigned
                check_violations (projectId, binding, globalVars["ADMIN_ROLE_REGEX"], globalVars["SVC_ACC_ADMIN_VIOLATION"], globalVars["SVC_ACC_REGEX"].format(projectId) )

                # Ideally check for specific admin permissions within the roles

        #
        # Retrieving this information makes the script 10 times slower than not doing it
        #
        #orgPolicy = cloudResourceManagerUtils.cloudresourcemanager_get_project_organisation_policy(projectId)
        #print "\n**********************\nORG POLICY:\n***************************\n{0}".format(json.dumps(orgPolicy))


    # Write the report to file
    dateString = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    writeReport(dateString)




if __name__ == '__main__':
    parser = argparse.ArgumentParser( description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-p', '--projects', required=True, metavar='project', nargs='+', help='List of one or more Google Cloud Project IDs where the actions will be performed.\nUse "-p all" to affect all projects.')
    args = parser.parse_args()
    main(args.projects)
# [END run]
