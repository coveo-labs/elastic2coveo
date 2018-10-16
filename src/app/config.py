#!/usr/bin/env python
### --------------------------------------------------------------------
### config.py
### --------------------------------------------------------------------
### Sets all Coveo URL's to call
### --------------------------------------------------------------------
import requests
import time

# constants
coveo_organization_id = ''
coveo_source_id = ''
coveo_push_api_key = ''
# constants
#coveo_organization_id = 'platformdemotb51i4qo'
#coveo_source_id = 'tupviyttjmlggnjzpeazbykhfu-platformdemotb51i4qo'
#coveo_push_api_key = 'xxeb705e89-f840-4f5d-8750-24c93dac2590'


#QA
#coveo_organization_id = 'demoelasticbellstagingpcehl8i8'
#coveo_source_id = 'xcazn2pv2r3kerwimw3a5hcpye-demoelasticbellstagingpcehl8i8'
#coveo_push_api_key = 'xx46e5275d-0aa4-4cd8-9155-6d372cd594a1'


# Endpoints
base_url = "https://push.cloud.coveo.com/v1/organizations/{organization_id}/"
coveo_document_api_url = base_url + "sources/{source_id}/documents"
coveo_status_api_url = base_url + "sources/{source_id}/status"
coveo_delete_older_than_url = base_url + "sources/{source_id}/documents/olderthan?orderingId={ordering_id}"
coveo_get_batch_file_id_url = base_url + "files"
coveo_batch_document_api_url = base_url + "sources/{source_id}/documents/batch?fileId={file_id}"

# construct Coveo API URLs
def setVar(args):
    global coveo_organization_id
    global coveo_source_id
    global coveo_push_api_key

    coveo_organization_id = args.porgid
    coveo_source_id = args.psourceid
    coveo_push_api_key = args.papi

def get_document_api_url():
    return coveo_document_api_url.format(
        organization_id = coveo_organization_id,
        source_id = coveo_source_id
    )

def get_batch_document_api_url(fileid):
    return coveo_batch_document_api_url.format(
        organization_id = coveo_organization_id,
        source_id = coveo_source_id,
        file_id= fileid
    )

def get_fileid_api_url():
    return coveo_get_batch_file_id_url.format(
        organization_id = coveo_organization_id
    )

def get_status_api_url():
    return coveo_status_api_url.format(
        organization_id = coveo_organization_id,
        source_id = coveo_source_id
    )

def get_delete_older_than_url(epoch_time_in_milliseconds):
    return coveo_delete_older_than_url.format(
        organization_id=coveo_organization_id,
        source_id=coveo_source_id,
        ordering_id=epoch_time_in_milliseconds
    )

# create Authorization (access_token) and content-type (json) headers
def get_headers_with_push_api_key():
    return {
        'Authorization': 'Bearer ' + coveo_push_api_key,
        'content-type': 'application/json'
    }

def delete_older_than(epoch_time_in_milliseconds):

    coveo_delete_older_than_url_for_call = get_delete_older_than_url(epoch_time_in_milliseconds)
    coveo_headers = get_headers_with_push_api_key()

    # print request
    print ('Calling: DELETE ' + coveo_delete_older_than_url_for_call + " " + str(coveo_headers))

    r = requests.delete(coveo_delete_older_than_url_for_call, headers=coveo_headers)

    print (r.status_code)
