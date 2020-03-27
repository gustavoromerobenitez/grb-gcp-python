#!/usr/bin/python
import os,sys
import argparse
import json
from googleapiclient import discovery

# Unit tests are supposed to be under the subdirectory tests/unit
# The common utils library is supposed to be located at the root of that path
# This is needed to find the google_resourcemanager_common_utils module since this Unit test is not within the same module
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
grandparentdir = os.path.dirname(parentdir)
sys.path.insert(0,grandparentdir)

import google_cloudresourcemanager_utils as utils

# [START run]
def main(pageSize = 0, requested_label = 'budget_owner'):
    utils.cloudresourcemanager_print_project_and_label_value(pageSize, requested_label)


if __name__ == '__main__':
    parser = argparse.ArgumentParser( description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-p','--pagesize', default=0, help='Optional argument that limits the number of Projects per Page returned by each API call. Only required for testing purposes.')

    parser.add_argument('--label', required='True', default='budget_owner', help='Select the label that you would like to find the value off')

    args = parser.parse_args()

    main(args.pagesize, args.label)

# [END run]
