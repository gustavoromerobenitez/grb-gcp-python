#!/usr/bin/python

from google.cloud import bigquery
from datetime import datetime

client = bigquery.Client()

for project in client.list_projects():
  try:
    for job in client.list_jobs(project = project.project_id, all_users = True, state_filter = "running"):
      elapsed_time = datetime.utcnow() - job.started.replace(tzinfo=None)
      print("{0}\t{1}\t{2}\t{3}\t{4}".format(job.job_id, job.user_email, project.project_id, job.started.strftime("%X %x"), str(elapsed_time)))
  except Exception as e:
    print(e)
