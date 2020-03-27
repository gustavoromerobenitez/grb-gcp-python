GRB-GCP-PYTHON

This is a collection of Python 2.7 helper libraries and scripts that interact with the Google Cloud APIs via the Python Client Library.

The scripts assume that:
- Python 2.7+, python-pip, Google Cloud SDK and the Python API Client Libraries are installed.
- You have enough permissions to interact with the respective services and have either logged in via `gcloud auth login` or have a GCP Service Account Key and the environment variable GOOGLE_APPLICATION_CREDENTIALS contains the path to the file that contains the private key
