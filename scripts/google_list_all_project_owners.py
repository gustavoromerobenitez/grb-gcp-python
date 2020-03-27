#!/usr/bin/python
import argparse
import os
import sys

# Unit tests are supposed to be under the subdirectory tests/unit
# The common utils library is supposed to be located at the root of that path
# This is needed to find the google_resourcemanager_common_utils module since this Unit test is not within the same module
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
import google_cloudresourcemanager_utils as cloudResourceManagerUtils
import google_constants as constants


# [START run]
def main(projectsArgumentList):

    if "all" in projectsArgumentList:
        projectList = cloudResourceManagerUtils.cloudresourcemanager_get_project_ids(projectFilter=constants.PROJECT_FILTER)
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

        members = cloudResourceManagerUtils.cloudresourcemanager_get_project_owners(projectId)

        if members is None:
            print("[ERROR] UNABLE TO RETRIEVE PROJECT IAM BINDINGS")
            print("[INFO] ======================================================================================")
        else:
            print("[INFO] ======================================================================================")
            for member in members:
                print("{0}".format(member))


if __name__ == '__main__':
    parser = argparse.ArgumentParser( description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-p', '--projects', required=True, metavar='project', nargs='+', help='List of one or more Google Cloud Project IDs where the actions will be performed.\nUse "-p all" to affect all projects.')
    args = parser.parse_args()
    main(args.projects)
# [END run]
