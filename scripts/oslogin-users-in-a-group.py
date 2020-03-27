#!/usr/bin/env python
#
# Given a GSuite group name, return the list of usernames in OS login format
#
# pip install --upgrade google-api-python-client
# to run:
# ./oslogin-users-in-a-group GSUITE_GROUP_NAME # Just outputs members of the group in a csv format
# ./oslogin-users-in-a-group -s GSUITE_GROUP_NAME USERNAME # outputs sudo rule to allow members of that group to sudo to username
#
#
# IF redirecting output to a file and using python2 invoke as:
# PYTHONIOENCODING=UTF-8
#./oslogin-users-in-a-group GSUITE_GROUP_NAME > file
#
# based on code from
# https://developers.google.com/admin-sdk/directory/v1/quickstart/python
#
from __future__ import print_function
import httplib2
import os
import sys
import json
from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

#
# The common utils library is supposed to be located in the parent directory
# Ideally all common function should be moved there to simplify future scripts
# This is needed to find the utils module since it is not within the same module
#
import inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)
sys.path.append(os.path.dirname)

import google_directory_utils as directory_utils

# If we selected sudo rule format, then we have a 2nd argument which is the username to target
# otherwise we just print out the list of usernames.
if sys.argv[1] == "-s":
  ingroup = sys.argv[2]
  inusername = sys.argv[3]
else:
  ingroup = sys.argv[1]


users = directory_utils.directory_get_group_members(groupKey = ingroup)

group_list = []
for user in users:
    group_list.append(user['email'].replace('.','_').replace('@','_'))

members = ",".join(group_list)

if sys.argv[1] == "-s":
  print(members + " ALL=(" + inusername + ") ALL")
else:
  print(members)
