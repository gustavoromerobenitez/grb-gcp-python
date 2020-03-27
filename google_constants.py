#!/usr/bin/python

###############################################
#
#  CONSTANTS
#
###############################################
PROJECT_LABEL = "billing_team"
PROJECT_LABEL_DEFAULT_VALUE = "grbgcp"
PROJECT_FILTER = "labels.{0}:{1}".format(PROJECT_LABEL, PROJECT_LABEL_DEFAULT_VALUE)

TRUE_REGEX = "^[Tt][Rr][Uu][Ee]$"
FALSE_REGEX = "^[Ff][Aa][Ll][Ss][Ee]$"


###############################################
#
# MANAGED VM SCHEDULE CONSTANTS
#
###############################################
MANAGED_INSTANCE_SCHEDULE_LABEL = "managed-instance-schedule"
MANAGED_INSTANCE_SCHEDULE_DEFAULT_VALUE = "enabled"
MANAGED_INSTANCE_SCHEDULE_PROJECT_FILTER = "{0} labels.{1}:{2}".format(PROJECT_FILTER, MANAGED_INSTANCE_SCHEDULE_LABEL, MANAGED_INSTANCE_SCHEDULE_DEFAULT_VALUE)

# Metadata Keys required for Instance Scheduling
ACTIVITY_WINDOW_KEY= "instance-activity-window"
STARTUP_DEPENDENCIES_KEY= "instance-startup-dependencies"
SHUTDOWN_DEPENDENCIES_KEY= "instance-shutdown-dependencies"

#
# Compute Instance Dependencies:
# Instances that should be RUNNING or TERMINATED before
# Dependencies are in the form (projectIID#)*(zone#)*(instanceName){1}(,(projectIID#)*(zone#)*(instanceName){1}){0,}
# If project or zone are not specified, the current project and zone will be used to look up the compute Instance
#
# Instance Naming Convention:  Name must start with a lowercase letter followed by up to 62 lowercase letters, numbers or hyphens, and cannot end with a hyphen
# Project Naming Convention:
# Zone Naming Convention:
ZONE_REGEX = "(africa|asia|australia|europe|northamerica|southamerica|us)\-(north|south|east|west|northeast|northwest|southeast|southwest|central)[0-9]+\-[a-z]"
COMPUTE_REGEX = "[a-z]([-a-z0-9]{0,61}[a-z0-9])?"

DEPENDENCY_REGEX = "(?:{0}\#){{0,1}}(?:{1}\#){{0,1}}(?:{2}){{1}}".format(COMPUTE_REGEX, ZONE_REGEX, COMPUTE_REGEX)
DEPENDENCIES_REGEX = "{0}(,{0})*".format(DEPENDENCY_REGEX)


# For time entries, ranges, * and lists are not supported
MINUTE_REGEX = "[0-5]{0,1}[0-9]"
HOUR_REGEX="(?:[0-1]{0,1}[0-9]|2[0-3])"
TIME_REGEX = "{0}:{1}".format(HOUR_REGEX, MINUTE_REGEX)


SINGLE_REGEX = "(?:{0})"
RANGE_REGEX = "(?:"+ SINGLE_REGEX + "(?:[\-]{0}){{0,1}})"
LIST_REGEX = "(?:"+ SINGLE_REGEX + "(?:[\,]"+ RANGE_REGEX +")*)"
SCHEDULE_REGEX_PATTERN = "(?:\*|"+ SINGLE_REGEX +"|"+ LIST_REGEX +"|"+ RANGE_REGEX +")"

DAY_OF_MONTH_REGEX = "(?:[0]{0,1}[1-9]|1[0-9]|2[0-9]|3[0-1])"
SCHEDULER_DAY_OF_MONTH_REGEX = SCHEDULE_REGEX_PATTERN.format(DAY_OF_MONTH_REGEX)

MONTHS_AS_TEXT_REGEX = "(?:[Jj][Aa][Nn]|[Ff][Ee][Bb]|[Mm][Aa][Rr]|[Aa][Pp][Rr]|[Mm][Aa][Yy]|[Jj][Uu][Nn]|[Jj][Uu][Ll]|[Aa][Uu][Gg]|[Ss][Ee][Pp]|[Oo][Cc][Tt]|[Nn][Oo][Vv]|[Dd][Ee][Cc])"
MONTH_REGEX = "(?:(?:[0]{{0,1}}[1-9]|1[0-2])|{0})".format(MONTHS_AS_TEXT_REGEX)
SCHEDULER_MONTH_REGEX = SCHEDULE_REGEX_PATTERN.format(MONTH_REGEX)

DAYS_OF_WEEK_AS_TEXT_REGEX = "(?:[Ss][Uu][Nn]|[Mm][Oo][Nn]|[Tt][Uu][Ee]|[Ww][Ee][Dd]|[Tt][Hh][Uu]|[Ff][Rr][Ii]|[Ss][Aa][Tt])"
DAY_OF_WEEK_REGEX = "(?:[0]{{0,1}}[0-6]|{0})".format(DAYS_OF_WEEK_AS_TEXT_REGEX)
SCHEDULER_DAY_OF_WEEK = SCHEDULE_REGEX_PATTERN.format(DAY_OF_WEEK_REGEX)

SCHEDULER_SCHEDULE_REGEX = "^{0}\s+{0}\s+{1}\s+{2}\s+{3}$".format(TIME_REGEX, SCHEDULER_DAY_OF_MONTH_REGEX, SCHEDULER_MONTH_REGEX, SCHEDULER_DAY_OF_WEEK)

MONTHS = { "JAN":1, "FEB":2, "MAR":3, "APR":4, "MAY":5, "JUN":6, "JUL":7, "AUG":8, "SEP":9, "OCT":10, "NOV":11, "DEC":12 }
DAYS_OF_WEEK = { "MON":0, "TUE":1, "WED":2, "THU":3, "FRI":4, "SAT":5, "SUN":6 }

SCHEDULE_ENTRY_TYPE_LIST = "LIST"
SCHEDULE_ENTRY_TYPE_LIST_WITH_RANGES = "LIST_WITH_RANGES"
SCHEDULE_ENTRY_TYPE_RANGE = "RANGE"
SCHEDULE_ENTRY_TYPE_SINGLE = "SINGLE"
SCHEDULE_ENTRY_TYPE_ANY = "ANY"
SCHEDULE_ENTRY_TYPE_TIME = "TIME"

LESS_OR_EQUAL = "<="
GREATER_OR_EQUAL = ">="
EQUAL = "=="


###############################################
#
# (DEPRECATED) MANAGED VM SHUTDOWN CONSTANTS
#
###############################################
MANAGED_INSTANCE_SHUTDOWN_LABEL = "managed-vm-shutdown"
MANAGED_INSTANCE_SHUTDOWN_DEFAULT_VALUE = "true"
MANAGED_INSTANCE_SHUTDOWN_PROJECT_FILTER = "{0} labels.{1}:{2}".format(PROJECT_FILTER, MANAGED_INSTANCE_SHUTDOWN_LABEL, MANAGED_INSTANCE_SHUTDOWN_DEFAULT_VALUE)

SHUT_DOWN_SCHEDULE_LABEL = "managed-shutdown-schedule"

DO_NOT_SHUTDOWN_VALUE = "never"
SHUTDOWN_DAILY_VALUE = "daily"
SHUTDOWN_WEEKLY_VALUE = "weekly"
SHUTDOWN_WEEKLY_VALUE = "monthly"
SHUTDOWN_SCHEDULE_NOT_SET = "not-set"



###############################################
#
#   MANAGED RESOURCE DELETION CONSTANTS
#
###############################################

MANAGED_RESOURCE_DELETION_LABEL = "managed-resource-deletion"
MANAGED_RESOURCE_DELETION_VALUE = "true"
MANAGED_RESOURCE_DELETION_PROJECT_FILTER = "{0} labels.{1}:{2}".format(PROJECT_FILTER, MANAGED_RESOURCE_DELETION_LABEL, MANAGED_RESOURCE_DELETION_VALUE)


GRACE_PERIOD_LABEL = "managed-deletion-grace-period"

DO_NOT_DELETE_VALUE = "do-not-delete"
GRACE_PERIOD_NOT_SET = "not-set"

# This makes sense for VMs but not for disks / buckets
GRACE_PERIOD_ONE_WEEK = "one-week-grace-period"
GRACE_PERIOD_ONE_MONTH = "one-month-grace-period"

MARKED_FOR_DELETION_LABEL = "marked-for-deletion"
MARKED_FOR_DELETION_VALUE_PREFIX = "on-or-after-"

MARKED_FOR_DELETION_MESSAGE = "\n[WARNING] [ Project {0} ] - Marked {1} {2} for Deletion on or after {3}."
