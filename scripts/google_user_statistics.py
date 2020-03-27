#!/usr/bin/env python
#
# pip install --upgrade google-api-python-client
# to run:
# ./gcp-user-statistics.py --report report-name
#
# IF redirecting output to a file and using python2 invoke as:
# PYTHONIOENCODING=UTF-8 ./user-audit.py --report users > users
#
# based on code from
# https://developers.google.com/admin-sdk/directory/v1/quickstart/python
#

from __future__ import print_function
import httplib2
import os
from time import sleep
import sys

from pprint import pprint
import json


#
# The common libraries are supposed to be located in the parent directory
#
import inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)
import google_directory_utils as directory_utils


def write_stderr(message):
    print(message, file=sys.stderr)

try:
    import argparse
    parser = argparse.ArgumentParser( description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--report', required='True', choices=['groupsets'])
    parser.add_argument('--persona', required='True',choices=['ro', 'devs','support', 'analyst','scientist','poc'])
    flags = parser.parse_args()
except ImportError:
    flags = None





def get_groupset_groups( groupset ):

    groups = directory_utils.directory_get_groups()
    groupset_groups = list()

    if not groups:
        print('[WARNING] No Groups in the the domain.')

    else:

        group_emails = set()
        for group in groups:
            group_email = group['email']
            group_emails.add(group_email)

        if groupset == 'devs':
            groupset_groups = filter(lambda k: "devs@grbgcpdevops.net" in k, group_emails)
        elif groupset == 'support':
            groupset_groups = filter(lambda k: 'support@grbgcpdevops.net' in k, group_emails)
        else:
            print('[WARNING] groupset {0} not known'.format(groupset))
            quit()

        return groupset_groups



#
# Gets the members on each group of a groupset
#
def get_groupset_members( groupset ):

    groupset_groups = get_groupset_groups(groupset)

    groupset_members = set()
    if not groupset_groups:
        print('[WARNING] No groups available in groupset {0}'.format(groupset))
    else:
        for group_email in groupset_groups:
            members = directory_utils.directory_get_group_members(group_email)
            if members == []:
                print('[WARNING] GROUP: {0} has no members'.format(group_email))
            else:
                for member in members:
                    member_email = member.get('email','(No Email Found)')
                    groupset_members.add(member_email)

    return groupset_members




#global Variables
def print_groupset_stats ( groupset ):

    groupset_members = get_groupset_members(groupset)
    groupset_groups = get_groupset_groups(groupset)

    print('Groupset: {0}'.format(groupset))
    print('Number of Groups: {0}'.format(len(groupset_groups)))
    print('Number of Users in Groups: {0}'.format(len(groupset_members)))


def main():
    exit()

if __name__ == '__main__':
    #print_groupset_stats(sys.argv[1])
    switcher = {
        'groupsets': print_groupset_stats
    }

    switcher.get(flags.report)(flags.persona)
