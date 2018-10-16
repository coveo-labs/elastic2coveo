# -*- coding: utf8 -*-
#!/usr/bin/env python
### --------------------------------------------------------------------
### push.py
### --------------------------------------------------------------------
### Will set the source status of the Coveo Platform
### Will execute the Upload to S3 and related Batch Push API calls to the Coveo Platform
### --------------------------------------------------------------------

import json
import os
import re
import csv
import urllib
import sys
import time
import requests
from datetime import timedelta 
from datetime import datetime

import config

# -----------------------------------------------------
# Update the source status in Coveo Cloud Platform
# -----------------------------------------------------
def set_source_status(status):
    # create statusType querystring parameter
    params = {
        'statusType': status
    }

    coveo_status_api_url = config.get_status_api_url()
    coveo_headers = config.get_headers_with_push_api_key()

    #print request
    print ('Calling: POST ' + coveo_status_api_url)
    print ('statusType: ' + status)

    # make POST request to change status
    r = requests.post(coveo_status_api_url, headers=coveo_headers, params=params)

    print (r.status_code)

# -----------------------------------------------------
# Batch Push API call
#   Will first get a S3 link/upload Uri
#   Upload the batch file to S3
#   Push the Batch file information to the Push API
# -----------------------------------------------------
def batchPush(jsoncontent, args):
    config.setVar(args)
    #first get S3 link / fileid
    coveo_fileid_api_url = config.get_fileid_api_url()
    coveo_headers = config.get_headers_with_push_api_key()
    print ('\n--------\nBATCH, step 1: Call FileId for S3: POST ' + coveo_fileid_api_url)
    #print ('Headers: ' + str(coveo_headers))
    r = requests.post(coveo_fileid_api_url, headers=coveo_headers)
    fileidjson=json.loads(r.text)
    print ("\nResponse from step 1: "+str(r.status_code))

    #create batch json
    print ("Response for S3: fileid=>"+fileidjson['fileId']+", uploaduri=>"+fileidjson['uploadUri'])
    coveo_batchdocument_api_url = config.get_batch_document_api_url(fileidjson['fileId'])
    print ('\n---------\nBATCH, step 2: Upload to s3\n')
    body = "{ \"AddOrUpdate\": [" + str(jsoncontent.decode('utf-8')) + "]}"
    r= requests.put(fileidjson['uploadUri'], headers={'Content-Type': 'application/octet-stream','x-amz-server-side-encryption': 'AES256'},data=body)
    print ('\nReturn from Upload call: '+str(r.status_code))

    #push to source
    print ('\n---------\nBATCH, setp 3: Push call to Cloud\n')
    r = requests.put(coveo_batchdocument_api_url, headers=coveo_headers)
    print ('\nReturn from Push call: '+str(r.status_code))
