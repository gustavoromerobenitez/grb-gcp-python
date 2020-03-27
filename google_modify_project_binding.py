#!/usr/bin/python
import argparse
import google_cloudresourcemanager_utils as cloudResourceManagerUtils
import google_constants as constants


# [START run]
def main(projectsArgumentList, operation, role, members):

    if "all" in projectsArgumentList:
        projectList = cloudResourceManagerUtils.cloudresourcemanager_get_project_ids(projectFilter=constants.PROJECT_FILTER)
    else:
        projectList = projectsArgumentList

    print("\n\n[INFO] ======================================================================================")
    print("[INFO] Removing Binding for {0} GCP Projects :".format(len(projectList)))
    for p in projectList:
        print("[INFO] {0}".format(p))
    print("[INFO] ======================================================================================")

    for projectId in projectList:

        print("\n\n[INFO] ======================================================================================")
        print("[INFO] Project: {0}".format(projectId))

        for member in members:
            print("\n[INFO] Member: {0} - Operation: {1} - role: {2}".format(member, operation, role))
            if operation == "add":
                cloudResourceManagerUtils.cloudresourcemanager_add_member_to_project_binding(projectId, role, member)
            elif operation == "remove":
                cloudResourceManagerUtils.cloudresourcemanager_remove_member_from_project_binding (projectId, role, member)


if __name__ == '__main__':
    parser = argparse.ArgumentParser( description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-p', '--projects', required=True, metavar='projects', nargs='+', help='List of one or more Google Cloud Project IDs where the actions will be performed.\nUse "-p all" to affect all projects.')
    parser.add_argument('-o', '--operation', choices=['add', 'remove'], required=True, metavar='operation', help='Operation to perform')
    parser.add_argument('-r', '--role', required=True, metavar='role', help='Role that identifies the binding')
    parser.add_argument('-m', '--members', required=True, metavar='members', nargs='+', help='Members to remove from the binding in the format user:username@<domain>  or serviceAccount:serviceAccountName@<projectName>.iam.gserviceaccount.com')
    args = parser.parse_args()
    main(args.projects, args.operation, args.role, args.members)
# [END run]
