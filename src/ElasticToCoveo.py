### --------------------------------------------------------------------
### ElasticToCoveo.py
### --------------------------------------------------------------------
### Will execute a query against Elastic search, for each shard one
### The Query results are then pushed (Batch) to a Coveo index (based on elastic)
### --------------------------------------------------------------------
### transformCoveoJSON
###   MUST BE ALTERED for your specific elastic index
###   Map elastic index fields to your coveo fields
### Dependencies:
###      python 3.+
###      pip install elasticsearch
### --------------------------------------------------------------------

from app.utils import parse_args, get_arg_parser, init_es
from app.shards import scan_shard, get_shards_to_routing
from multiprocessing import Pool,Value, RLock, Lock
from app.push import set_source_status, batchPush
import app.config
import json
import os
import time
import ctypes
from datetime import timedelta 
from datetime import datetime
import time
import zlib
import base64

currentjson = Value(ctypes.c_char_p, b"")
maxpush = (15*1024*1024) #15 Mb
lock = Lock()

# -----------------------------------------------------
# Add the currentjson to the current batch
# If batch is to high (maxpush), execute the batchPush command
# -----------------------------------------------------
def addToBatchJson( jsonp, lock, currentjson, args):
    global maxpush
    with lock:
        if (currentjson.value==b""):
            currentjson.value = json.dumps(jsonp).encode('utf-8')
        else: 
            currentjson.value =  currentjson.value +b","+ json.dumps(jsonp).encode('utf-8')
        #print (currentjson.value)
        if (len(currentjson.value)>(maxpush)):
            #New batch request
            batchPush(currentjson.value, args)
            currentjson.value=""

# -----------------------------------------------------
# transformToCoveoJSON
# Transform the elastic Json to a Coveo Json
# Include mandatory fields and/or enable additional metadata fields
# By default all _source fields are already mapped to Json fields
# -----------------------------------------------------
def transformToCoveoJSON( doc ):
    global pool
    # Mandatory documentId field
    doc['documentId']="https://"+doc['_index']+"/"+doc['_id']
    # Uri for the index
    doc['uri']="https://"+doc['_index']+"/"+doc['_id']
    # Clickable uri, where people click on
    doc['clickableuri']='uri'

    try:
        ### ---------------------------------------------------------
        ### Add additional fields to map (always custom work!!!)
        ### ---------------------------------------------------------
        #Map author
        #doc['myauthor'] = doc['_source']['Author']
        #print( doc['_source']['body'])

        #Built HTML for Coveo's quickview
        if ('body' in doc['_source']):
          content = str (doc['_source']['body'])
          compresseddata = zlib.compress(content.encode('utf-8'), zlib.Z_BEST_COMPRESSION) # Compress the file content
          encodeddata = base64.b64encode(compresseddata)  # Base64 encode the compressed content
          doc['CompressedBinaryData']= encodeddata.decode('utf-8')
        ### ---------------------------------------------------------

        #Map all _source fields to Json fields
        for fields in doc['_source']:
            doc[fields] = doc['_source'][fields]
        doc['_source']=''
    except Exception as error:
        print ("Error at mapping (TransformToCoveoJSON): "+format(error))
        pool.terminate()

    return doc


# -----------------------------------------------------
# processDoc
# Called for each Elastic Search Result
# -----------------------------------------------------
def processDoc( doc, args, routing, lock, currentjson ):
    doc = transformToCoveoJSON( doc )
    print ("Processing from routing: "+str(routing)+" doc: "+str(doc['documentId']))
    
    addToBatchJson(doc, lock, currentjson, args)

# -----------------------------------------------------
# worker for one shard scan
# -----------------------------------------------------
def worker(args, routing ): 
    global pool
    _es = init_es(args)
    
    currentjson = Value(ctypes.c_char_p, b"")
    lock = Lock()
    #Check if we have an incremental refresh or not
    try:
      if (args.iq==''):
        query = json.loads(args.q) 
      else:
        query = json.loads(args.iq.replace("[REFRESH_DATE]", args.id))
    except Exception as error:
        print ("Error at worker, loading query (worker): "+format(error))
        pool.terminate()

    #print (query)
    scan_shard(_es, args.index, '', query, routing, processDoc, args, currentjson, lock )

    #Last Push
    if (currentjson.value!=b""):
        batchPush(currentjson.value, args)

def init_child(lock_, json_):
    global lock
    global currentjson
    lock = lock_
    currentjson = json_

if __name__ == '__main__':
    onlylatest = False

    parser = get_arg_parser()
    args = parse_args(parser)
    
    app.config.coveo_organization_id = args.porgid
    app.config.coveo_source_id = args.psourceid
    app.config.coveo_push_api_key = args.papi
    #current date = datetime.datetime.today().strftime('%Y-%m-%d')
    es = init_es(args)
    lastrefresh= datetime.today().strftime('%Y-%m-%d')
    #Set source status
    if (args.iq==''):
      set_source_status('REBUILD')
      onlylatest = False
    else:
      set_source_status('INCREMENTAL')
      onlylatest = True
      #Check args
      if args.id == '':
        lastrefresh= datetime.today().strftime('%Y-%m-%d')
      else:
        lastrefresh = args.id
      #File is always leading
      if os.path.isfile(args.index+'_last_refresh.dat'):
        with open(args.index+'_last_refresh.dat', 'r') as file:
          lastrefresh = file.read()
          args.id = lastrefresh
      
    #currentjson = ''
    
    # set beginning time
    epoch_time_in_milliseconds = int(round(time.time() * 1000))

    shards_to_routing = get_shards_to_routing(es, args.index)#, args.doc_type)
    print(shards_to_routing)

    pool = Pool(initializer=init_child,  initargs=(lock, currentjson))
    jobs = []
    for shard, routing in shards_to_routing.items():
        print ("shard: "+str(shard)+", routing: "+str(routing))
        
        p = pool.apply_async(worker, args=(args, routing, ))

    pool.close()
    pool.join()

    #Set source status
    if onlylatest==False:
        app.config.setVar(args)
        app.config.delete_older_than(epoch_time_in_milliseconds)

    # set status back to IDLE
    set_source_status('IDLE')

    # update last refresh date
    currentdate = datetime.today().strftime('%Y-%m-%d')
    with open(args.index+'_last_refresh.dat', 'w') as file:
      file.write(currentdate)


