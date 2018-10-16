# elastic2coveo
Script to convert an existing elasticsearch index to Coveo on Elasticsearch.
All content from the target will be uploaded to the Coveo on Elasticsearch index.

## Description
If you have an existing elasticsearch index and you want to use that data with the Coveo Platform you must re-index the elasticsearch index.  
This script will help you to do that.

It uses multiple components:
* __Coveo platform__ - hosts the Coveo index and organization for your data, provides the search capabilities.
* __elasticsearch__ - hosts your existing elasticsearch index.
* __Push API__ - Coveo's push API to push content into the Coveo index.
* __scan (scroll) api__ - The scan/scroll api of elasticsearch to retrieve the results.

## How it works
The script will connect to your elasticsearch index using the [Python Elasicsearch library](https://elasticsearch-py.readthedocs.io/en/master/).
It will collect all shard information from your elasticsearch index and per shard a scan (scroll) call is being made to retrieve all results.
For each document retrieved a call is being made to the ```processDoc``` function. This will process the document, add additional JSON data for the Coveo indexer and pushes the content to your Coveo Index using the [Batch Push API](https://docs.coveo.com/en/54).

## How to configure
Before you can use the script you must configure the method ```transformToCoveoJSON``` in file ```ElasticToCoveo.py```. This method will transfer the JSON result retrieved from your elasticsearch index into a JSON, suitable for the Push API of Coveo. Make sure you set the following fields properly:
```python
    # Mandatory documentId field
    doc['documentId']="https://"+doc['_index']+"/"+doc['_id']
    # Uri for the index
    doc['uri']="https://"+doc['_index']+"/"+doc['_id']
    # Clickable uri, where people click on
    doc['clickableuri']='uri'
``` 
All ```_source``` fields from elastic will already be mapped automatically.

### Example, add metadata field accountname
If your elasticsearch index contains a field called ```_source.accountname``` and you want to map that to a Coveo fieldname, you must add the following to ```transformToCoveoJSON```:
```python
doc['sfaccountname'] = doc['_source']['accountname']
```
Then in your Coveo Push source you define a [Field Mapping](https://docs.coveo.com/en/144/), which maps the field with the name ```sfaccountname``` to ```%[sfaccountname]```.

### Example, construct a Coveo HTML preview from your elasticsearch data
If you elasticsearch index contains a field with HTML data, this data can be used in the Coveo UI as a [preview/quickview component](https://coveo.github.io/search-ui/components/quickview.html). In order to do so, you must use the following code in ```transformToCoveoJSON``` to define the proper content:
```python
#Built HTML for Coveo's quickview
if ('body' in doc['_source']):
  content = str (doc['_source']['body'])
  compresseddata = zlib.compress(content.encode('utf-8'), zlib.Z_BEST_COMPRESSION) # Compress the file content
  encodeddata = base64.b64encode(compresseddata)  # Base64 encode the compressed content
  doc['CompressedBinaryData']= encodeddata.decode('utf-8')
```
In the above example, our ```body``` field in elasticsearch contains our HTML (see [CompressedBinaryData](https://docs.coveo.cm/en/164)).

## How to run
Before you run the script, first install the Dependencies.  
Then follow the Startup parameters explanation.

### Dependencies
* [Python 3.x](https://www.python.org/downloads/)
* [Elasticsearch index](https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html)
* [Python Elasticsearch Client](https://elasticsearch-py.readthedocs.io/en/master/)
* [Python Requests library]
* [Coveo Push Source](https://docs.coveo.com/en/92), Step 0 and Step 1

### Startup parameters
For an example see: ElasticToCoveo.bat and ElasticToCoveoIncremental.bat (incremental update).
#### -index
The name of the elasticsearch index.  
For example: ```mynewindex```

#### -porgid
The Coveo Organization ID where the Push source is defined.  
For example: ```platformdemoestic3zlf3p```

#### -psourceid
The Coveo Organization Source Id of the Push source.  
For example: ```tw43i2amxl3nk7m54wertsnxy-platformdemoelastic3ee3f2p```

#### -papi
The Coveo Organization Push API key.  
For example: ```xx4f3ee53-26e5-4fc4-b924-75de4edda6e5```

#### --q
The Query to execute in elasticsearch.   
For example: ```{"query":{"match": {"source": "myTest" }} }```  
Default: {"query": {"match_all": {}}}  
After the full query is being executed and uploaded (pushed) to the Coveo index, all old content will be removed from the Coveo index.

#### --iq
The Incremental Query to execute in elasticsearch, refresh date [REFRESH_DATE] should be present in the query.   
For example: ```{"query": { "range" : {  "date": { "gte": "[REFRESH_DATE]" }}}}```  
The Incremental Query will NOT remove old content from the Coveo index.  
Currently the update is done on a dialy based. The last refresh date is saved in the file ```[index]_last_refresh.dat```.

#### --id
The date to use for the Incremental Query, normally loaded from disk.  
For example: ```YYYY-MM-DD```

#### -es-host
The elasticsearch hostname.  
For example: ```1baff89a12a5a0240647866b4aa95.us-east-1.aws.found.io```

#### -es-port
The elasticsearch host port.  
For example: ```9200```

#### -es-auth
The elasticsearch username:password.  
For example: ```elastic:DEWWYuu66hNZ6z7M5NMW``` (username:password)

#### --es-use-ssl
If SSL must be used when connecting to elasticsearch.

Examples:
Full replication of the index:  
```python ElasticToCoveo.py -index mynewindex -porgid "platformdemoelastic3zlx2p" -psourceid "tw43i2amxl3nk7m54llgrtxesnxy-platformdemoelastidsc3zlf3f2p" -papi "xx4f3exe53-2sa5-4fc4-b924-75de4edda6e5" -es-host 1baff89a12a5a0240647866b4ab95.us-east-1.aws.found.io -es-port 9200 -es-auth "elastic:DEW66h0jQNZ6z7M5NMWr"```

  
Incremental replication of the index:  
```python ElasticToCoveo.py -index mynewindex --iq "{\"query\": { \"range\" : {  \"date\": { \"gte\": \"[REFRESH_DATE]\" }}}}" -porgid "platformdemoestic3zlf3p" -psourceid "tw43i2amxl3nk7m54wertsnxy-platformdemoelastic3ee3f2p" -papi "xx4f3ee53-26e5-4fc4-b924-75de4edda6e5" -es-host 1baff89a12a5a0240646b4aae9b95.us-east-1.aws.found.io -es-port 9200 -es-auth "elastic:DEWWYuu0jQNZ6z7M5NMWr"```

### References
* [ES Scan Master](https://github.com/amityo/es-parallel-scan)

### Authors
- Wim Nijmeijer (https://github.com/wnijmeijer)


