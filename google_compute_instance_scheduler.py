#!/usr/bin/python
import sys
import re
import argparse
import time
import datetime as dt
import json
import googleapiclient.discovery
import google_constants as constants
import google_compute_utils as computeUtils
import google_cloudresourcemanager_utils as cloudResourceManagerUtils
from googleapiclient.errors import HttpError


#
#
#
def get_instance_activity_window(project, zone, instanceResource, metadataKey):

    schedule = computeUtils.compute_get_metadata_value(project, zone, instanceResource['name'], metadataKey)

    if schedule != None:

        schedule = schedule.strip()
        if re.search(constants.SCHEDULER_SCHEDULE_REGEX, schedule):
            return schedule
        else:
            print "[ERROR] Metadata Key {0} on VM instance {1} is not a valid VM Activity Window.\n[ERROR] Please follow standard crontab syntax and use Ranges or Lists rather than single values if possible.\n[ERROR] The following special characters are not supported / < >, including the functionality the they support in Crontab".format(metadataKey, instanceResource['name'])
            return None
    else:
        print "[INFO] Metadata Key {0} not found in VM instance {1}".format(metadataKey, instanceResource['name'])
        return None



#
# Returns a list of dependecies extracted from the value associated with the given metadata key
#
def get_instance_dependencies(project, zone, instanceResource, metadataKey):

    dependencies = computeUtils.compute_get_metadata_value(project, zone, instanceResource['name'], metadataKey)

    if dependencies != None:

        dependecies = dependencies.strip()

        if re.search(constants.DEPENDENCIES_REGEX, dependencies):
            return dependencies.split(",")
        else:
            print "[ERROR] Metadata Key {0} on Compute Instance {1} is not a valid Instance Dependency declaration.\n[ERROR] The supported format is: instancePath(,instancePath)* where instancePath can be the instance name or optionally can include the project name and the zone name:  projectID#zone#instance(,projectID#zone#instance)*".format(metadataKey, instanceResource['name'])
            return None
    else:
        print "[INFO] Metadata Key {0} not found in Compute Instance {1}".format(metadataKey, instanceResource['name'])
        return None



#
# Given a Metadata Key that points to a list of dependencies, this function checks if the dependency checks or not
# Each dependency is a list of Compute Instances specified by strings of the form: project#zone#instanceName / project#instanceName / instanceName / zone#instanceName
# At the moment there are just Startup and Shutdown dependencies
# - A Compute Instace will not start up unless all the instances in the dependency list are in a RUNNING state
# - Likewise a Compute Instance will not be shut down unless all the instances in the dependency list are in a TERMINATED state
#
def check_instance_dependencies(project, zone, instanceResource, metadataKey):

    dependencies = get_instance_dependencies(project, zone, instanceResource, metadataKey)
    checksPassed = True

    if dependencies != None:

        for dependency in dependencies:

            dependencyProject = project
            dependencyZone = zone

            if re.search("#", dependency):

                fields = dependency.split("#")

                if len(fields) == 3:

                    dependencyProject = fields[0]
                    dependencyZone = fields[1]
                    dependencyInstanceName = fields[2]

                elif len(fields) == 2:

                    dependencyInstanceName = fields[1]
                    if re.search(constants.ZONE_REGEX, fields[0]):
                        dependencyZone = fields[0]
                    else:
                        dependencyProject = fields[0]
                else:
                    dependencyInstanceName = fields[0]
            else:
                dependencyInstanceName = dependency

            dependencyInstanceResource = computeUtils.compute_get_instance(dependencyProject, dependencyZone, dependencyInstanceName)

            if dependencyInstanceResource != "":
                print '[INFO] Dependency Instance {0} - Status: {1}'.format(dependencyInstanceName, dependencyInstanceResource['status'])

                if metadataKey == constants.SHUTDOWN_DEPENDENCIES_KEY and dependencyInstanceResource['status'] != computeUtils.TERMINATED:
                    print "[WARNING] Dependency Failed"
                    checksPassed = False
                    break

                elif metadataKey == constants.STARTUP_DEPENDENCIES_KEY and dependencyInstanceResource['status'] != computeUtils.RUNNING:
                    checksPassed = False
                    print "[WARNING] Dependency Failed"
                    break
            else:
                print '[WARNING] Dependency NOT Found: Instance {0} - Project {1} - Zone {2}'.format(dependencyInstanceName, dependencyProject, dependencyZone)

    else:
        print '[INFO] No Dependencies Found'

    if checksPassed:
        print '[INFO] All dependency checks passed'
    else:
        print '[WARNING] Dependency checks failed. Read previous messages to find out the failed dependency.'

    return checksPassed





#
# Gets the Integer equivalent to the Schedule values
#
def get_integer_values(originalValues):

    values = []

    for originalValue in originalValues:

        if not re.match("^\d+$", originalValue):

            if re.match(constants.DAYS_OF_WEEK_AS_TEXT_REGEX, originalValue):
                dayOfWeek = originalValue.upper()
                values.append( int(constants.DAYS_OF_WEEK[dayOfWeek]) )

            elif re.match(constants.MONTHS_AS_TEXT_REGEX, originalValue):
                month = originalValue.upper()
                values.append( int(constants.MONTHS[month]) )

        else:
            values.append(int(originalValue))

    return values

#
# Creates a Dict reoresentiung the Schedule Entry and its type
# Converts text entries into their Integer values for simplicity
#
# * => ANY
# 2 => SINGLE
# 2,15,27 or  SUN, MON, TUE => LIST
# 2-12 or JAN-APR => RANGE
#
# The schedule Field has already passed a Regex match check, therefore it is presumed valid
#
def get_schedule_entry(scheduleField):

    scheduleEntry = {}

    if scheduleField == "*":
        scheduleEntry["type"] = constants.SCHEDULE_ENTRY_TYPE_ANY
        scheduleEntry["values"] = [scheduleField]

    elif re.search(",", scheduleField):
        scheduleEntry["type"] = constants.SCHEDULE_ENTRY_TYPE_LIST
        scheduleEntry["values"] = []
        potentialValues = scheduleField.split(",")
        for potentialValue in potentialValues: # Lists can contain ranges too

            if re.search("-", potentialValue):
                scheduleEntry["type"] = constants.SCHEDULE_ENTRY_TYPE_LIST_WITH_RANGES
                rangeValues = get_integer_values(potentialValue.split("-"))
                minValue = rangeValues[0]
                maxValue = rangeValues[1]
                currentValue = minValue
                while currentValue <= maxValue:
                    scheduleEntry["values"].append(currentValue)
                    currentValue+=1
            else:
                for integerValue in get_integer_values([potentialValue]):
                    scheduleEntry["values"].append(integerValue)


    elif re.search("-", scheduleField):
        scheduleEntry["type"] = constants.SCHEDULE_ENTRY_TYPE_RANGE
        scheduleEntry["values"] = get_integer_values(scheduleField.split("-"))

    elif re.search(constants.TIME_REGEX, scheduleField):
        scheduleEntry["type"] = constants.SCHEDULE_ENTRY_TYPE_TIME
        scheduleEntry["values"] = [scheduleField]
    else:
        scheduleEntry["type"] = constants.SCHEDULE_ENTRY_TYPE_SINGLE
        scheduleEntry["values"] = get_integer_values([scheduleField])

    return scheduleEntry



#
# Matches a current value taken from datetime.now() with the schedule set for the VM
# Tolerance applies only to SINGLE values and is used to compare MINUTES only
# The reason is that this schedule will run every 15 or so and is not exact
# (not like crontab which runs every minute)
def check_if_schedule_entry_checks_out (scheduleEntry, currentValue, checkType = constants.EQUAL):

    entryChecksOut = False

    # * Matches everything
    if scheduleEntry["type"] == constants.SCHEDULE_ENTRY_TYPE_ANY:
        #print "[DEBUG] [SUCCESS] Schedule Entry (Type:{0} Value:{1}) matches Current Value: {2}".format(scheduleEntry["type"], scheduleEntry["values"], currentValue)
        entryChecksOut = True

    elif scheduleEntry["type"] == constants.SCHEDULE_ENTRY_TYPE_SINGLE:
        scheduleIntValue = int(scheduleEntry["values"][0])
        if currentValue == scheduleIntValue:
            #print "[DEBUG] [SUCCESS] Schedule Entry (Type:{0} Value:{1}) matches Current Value: {2}".format(scheduleEntry["type"], scheduleEntry["values"], currentValue)
            entryChecksOut = True

    elif scheduleEntry["type"] == constants.SCHEDULE_ENTRY_TYPE_RANGE:
        scheduleMinIntValue = int(scheduleEntry["values"][0])
        scheduleMaxIntValue = int(scheduleEntry["values"][1])
        if currentValue >= scheduleMinIntValue and currentValue <= scheduleMaxIntValue:
            #print "[DEBUG] [SUCCESS] Schedule Entry (Type:{0} Value(s):{1}) contain the current value: {2}".format(scheduleEntry["type"], scheduleEntry["values"], currentValue)
            entryChecksOut = True

    elif ( scheduleEntry["type"] == constants.SCHEDULE_ENTRY_TYPE_LIST
           or scheduleEntry["type"] == constants.SCHEDULE_ENTRY_TYPE_LIST_WITH_RANGES):
        for value in scheduleEntry["values"]:
            entryChecksOut = (entryChecksOut or currentValue == int(value))
        #if entryChecksOut:
        #    print "[DEBUG] [SUCCESS] Schedule Entry (Type:{0} Value(s):{1}) matches Current Value: {2}".format(scheduleEntry["type"], scheduleEntry["values"], currentValue)

    elif ( scheduleEntry["type"] == constants.SCHEDULE_ENTRY_TYPE_TIME ):

        (entryHour, entryMinute) = scheduleEntry["values"][0].split(":")
        entryTime = dt.time( hour = int(entryHour), minute = int(entryMinute) )

        (currentHour, currentMinute) = currentValue.split(":")
        currentTime = dt.time( hour = int(currentHour), minute = int(currentMinute) )

        if checkType == constants.GREATER_OR_EQUAL:
            entryChecksOut = ( currentTime >= entryTime )

        elif checkType == constants.LESS_OR_EQUAL:
            entryChecksOut = ( currentTime <= entryTime )

        else:
            entryChecksOut = ( currentTime == entryTime )

        #if entryChecksOut:
        #    print "[DEBUG] [SUCCESS] Schedule Entry (Type:{0} Value(s):{1}) is {2} Current Value: {3}".format(scheduleEntry["type"], scheduleEntry["values"], checkType, currentValue)

    #if not entryChecksOut:
    #    print "[DEBUG] [FAILURE] Schedule Entry (Type:{0} Value(s):{1}) failed checks - Current Value: {2}".format(scheduleEntry["type"], scheduleEntry["values"], currentValue)

    return entryChecksOut





#
# Checks
#
def check_instance_activity_window(instanceResource, schedule):

    currentStatus = instanceResource['status']

    now = dt.datetime.now()
    currentTime = now.strftime("%H:%M")
    currentDayOfMonth = int(now.strftime("%d"))
    currentMonth = int(now.strftime("%m"))
    currentDayOfWeek = int(dt.datetime.today().weekday())

    # Split the fields of the Crontab-like activity window definition
    scheduleFields = schedule.split(" ")
    scheduleStartTime = get_schedule_entry(scheduleFields[0])
    scheduleEndTime = get_schedule_entry(scheduleFields[1])
    scheduleDayOfMonth = get_schedule_entry(scheduleFields[2])
    scheduleMonth = get_schedule_entry(scheduleFields[3])
    scheduleDayOfWeek = get_schedule_entry(scheduleFields[4])


    # Function to check if a value is within the activity window definition
    withinActivityWindow = True
    withinActivityWindow = withinActivityWindow and check_if_schedule_entry_checks_out (scheduleMonth, currentMonth)
    withinActivityWindow = withinActivityWindow and check_if_schedule_entry_checks_out (scheduleDayOfMonth, currentDayOfMonth)
    withinActivityWindow = withinActivityWindow and check_if_schedule_entry_checks_out (scheduleDayOfWeek, currentDayOfWeek)
    withinActivityWindow = withinActivityWindow and check_if_schedule_entry_checks_out (scheduleEndTime, currentTime, checkType = constants.LESS_OR_EQUAL)
    withinActivityWindow = withinActivityWindow and check_if_schedule_entry_checks_out (scheduleStartTime, currentTime, checkType = constants.GREATER_OR_EQUAL)

    if not withinActivityWindow:
        print "[INFO] OUTSIDE Activity Window: {0} (Current Time {1})".format(schedule, now)
    else:
        print "[INFO] WITHIN Activity Window: {0} (Current Time {1})".format(schedule, now)

    return withinActivityWindow






# [START run]
def main(projectsArgumentList, zone):

    print "\n\n[INFO] ======================================================================================"

    if "all" in projectsArgumentList:
        projectList = cloudResourceManagerUtils.cloudresourcemanager_get_project_ids(projectFilter = constants.MANAGED_INSTANCE_SCHEDULE_PROJECT_FILTER)
        print "[INFO] Projects where Compute Instance scheduling is ENABLED (via {0}):\n[INFO] {1}".format(constants.MANAGED_INSTANCE_SCHEDULE_LABEL, projectList)
    else:
        projectList = projectsArgumentList
        print "[INFO] Projects provided: {0}".format(projectList)

    print "[INFO] ======================================================================================"


    for project in projectList:

        print "\n\n[INFO] ======================================================================================"
        print "[INFO] Project: {0}".format(project)
        print "[INFO] Zone: {0}".format(zone)

        instances = []
        try:

            # If the projects have been given in the command line, check whether they are managed or not
            if not cloudResourceManagerUtils.checkIfProjectHasLabel(project, constants.MANAGED_INSTANCE_SCHEDULE_LABEL, constants.MANAGED_INSTANCE_SCHEDULE_DEFAULT_VALUE) :
                print "[ERROR] **********  Compute Instance Scheduling NOT enabled  **************"
                print "[INFO] ======================================================================================"
                continue

            instances = computeUtils.compute_list_instances(project, zone)
            print "[INFO] # of Compute Instances: {0}".format(len(instances))
            print "[INFO] ======================================================================================"

        except HttpError as e:
            print "[ERROR] **********  PROJECT NOT FOUND  **************"
            print "[INFO] ======================================================================================"
            continue


        for instanceResource in instances:

            print "\n\n[INFO] Instance: {0}".format(instanceResource['name'])

            # Check the status of the instance. It can be one of the following values:
            # PROVISIONING, STAGING, RUNNING, STOPPING, STOPPED, SUSPENDING, SUSPENDED, and TERMINATED.
            currentStatus = instanceResource['status']
            print "[INFO] Status: {0}".format(currentStatus)

            # TODO: Allow more than one Start-up and Shutdown Schedules (Weekdays/Weekends, etc)
            # Get Shutdown and Startup schedules from the instance metadata
            activityWindow = get_instance_activity_window(project, zone, instanceResource, constants.ACTIVITY_WINDOW_KEY)

            # Check the target status given the current time and the schedule and decide what actions are required: STOP/START/WAIT
            # print "[INFO] Checking Activity Window: {0}".format(activityWindow)

            if activityWindow != None:

                scheduleCheck = check_instance_activity_window(instanceResource, activityWindow)

                if currentStatus == "RUNNING" and not scheduleCheck: # Outside of Activity Window
                    if check_instance_dependencies(project, zone, instanceResource, constants.SHUTDOWN_DEPENDENCIES_KEY):
                        computeUtils.compute_perform_operation_on_instance(project, zone, instanceResource["name"], computeUtils.COMPUTE_STOP_OPERATION, computeUtils.OPERATION_RUNNING)
                    else:
                        print "[INFO] Shutdown Dependency found. No action taken at this time"
                elif currentStatus == "TERMINATED" and scheduleCheck: # Within Acivity Window
                    if check_instance_dependencies(project, zone, instanceResource, constants.STARTUP_DEPENDENCIES_KEY):
                        computeUtils.compute_perform_operation_on_instance(project, zone, instanceResource["name"], computeUtils.COMPUTE_START_OPERATION, computeUtils.OPERATION_RUNNING)
                    else:
                        print "[INFO] Start Up Dependency found. No action taken at this time"
                else:
                    print "[INFO] No action required at this time"




if __name__ == '__main__':
    parser = argparse.ArgumentParser( description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-p','--projects', required=True, metavar='project', nargs='+', help='List of one or more Google Cloud projects where the actions will be performed.\nUse "-p all" to affect all "managed" projects, i.e.: Projects with a label called '+constants.MANAGED_INSTANCE_SHUTDOWN_LABEL+' set to true) .')
    parser.add_argument('-z','--zone', default='europe-west1-b', help='Optional Compute Engine zone where the actions will be performed.')
    args = parser.parse_args()
    main(args.projects, args.zone)
# [END run]
