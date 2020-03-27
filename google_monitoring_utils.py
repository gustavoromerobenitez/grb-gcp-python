#!/usr/bin/python
import sys
import re
import time
from google.cloud import monitoring_v3

################################################################################
#
#   GOOGLE MONITORING COMMON FUNCTIONS
#
#   This library has just been started as an example
#   of how to interact with the monitoring API
#
#  Every Service has a different metrics Prefix
#
#  Metrics are often only avialable after a period of time
#  Some Metrics have a sampling delta which means there is one
#  point of data every Delta seconds
#
###############################################################################

# https://cloud.google.com/monitoring/api/metrics_gcp#gcp-compute
COMPUTE_METRICS_PREFIX = "compute.googleapis.com/"
COMPUTE_METRIC_CPU_UTILISATION = COMPUTE_METRICS_PREFIX + "instance/cpu/utilization"
COMPUTE_METRIC_UPTIME = COMPUTE_METRICS_PREFIX + "instance/uptime"


# https://cloud.google.com/monitoring/api/metrics_gcp#gcp-dataproc
DATAPROC_METRICS_PREFIX = "dataproc.googleapis.com/"

# Some metrics are only available after a few minutes
METRIC_AVAILABILITY_DELAY = 300
METRIC_AVAILABILITY_SAMPLING_DELTA = 60


#
# Returns a list of TimeSeries Objects
#
def monitoring_list_metric(project_id, metricName, interval = None):
    client = monitoring_v3.MetricServiceClient()
    project_name = client.project_path(project_id)

    if interval == None:
        interval = monitoring_v3.types.TimeInterval()
        now = time.time()
        interval.end_time.seconds = int(now - METRIC_AVAILABILITY_DELAY)
        interval.start_time.seconds = int(now - METRIC_AVAILABILITY_DELAY - METRIC_AVAILABILITY_SAMPLING_DELTA)

    # https://googleapis.github.io/google-cloud-python/latest/monitoring/gapic/v3/api.html#google.cloud.monitoring_v3.MetricServiceClient.list_time_series
    results = client.list_time_series(
        project_name,
        'metric.type = "{0}"'.format(metricName),
        interval,
        monitoring_v3.enums.ListTimeSeriesRequest.TimeSeriesView.FULL)

    return list(results)


def test_consume_uptime_metric():
    uptimeString = ""
    uptimeResults = utils.monitoring_list_metric(project, utils.COMPUTE_METRIC_UPTIME)
    if uptimeResults != []:
        uptimeString = str(uptimeResults[0].points[0].interval.end_time.seconds) # TimeSeries Object
