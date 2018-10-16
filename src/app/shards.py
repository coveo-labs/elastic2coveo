### --------------------------------------------------------------------
### shards.py
### --------------------------------------------------------------------
### Gets the shard routing information from an Elastic Search index
### Will execute a scroll api call for each shard (scan command) 
### --------------------------------------------------------------------
from collections import namedtuple

from elasticsearch.helpers import scan

ShardInfo = namedtuple("ShardInfo", "routing address")

# -----------------------------------------------------
# Get all shards from the target Elastic Index and retrieve all routing parameters
# -----------------------------------------------------
def get_shards_to_routing(client, index):#, doc_type):
    shards_info = client.search_shards(index) #, doc_type)
    number_of_shards = len(shards_info['shards'])

    shards = {}
    i = 0

    while len(shards.keys()) < number_of_shards:
        #r = client.search_shards(index, doc_type, routing=i)
        r = client.search_shards(index, routing=i)
        shard_number = r['shards'][0][0]['shard']
        if shard_number not in shards:
            shards[shard_number] = i
        i += 1

    return shards


def get_shards_info(client, index, doc_type):
    """
    Returns a mapping between shard number to the shards' information - routing and address.
    """
    shards_info = client.search_shards(index) #, doc_type)
    number_of_shards = len(shards_info['shards'])
    nodes = _get_nodes_to_address(shards_info)

    shards_info = {}
    i = 0

    while len(shards_info.keys()) < number_of_shards:
        #result = client.search_shards(index, doc_type, routing=i)
        result = client.search_shards(index, routing=i)
        shard = _get_primary_shard(result)

        shard_number = shard['shard']
        node = shard['node']
        address = nodes[node]

        if shard_number not in shards_info:
            shards_info[shard_number] = ShardInfo(routing=i, address=address)
        i += 1

    return shards_info

# -----------------------------------------------------
# Call scroll api (scan) from Elastic search and provide results to Coveo Index
# -----------------------------------------------------
def scan_shard(client, index, doc_type, query, routing, func, args, currentjson, lock):
    """
    Scans a specific shard by routing number.
    
    :param client: es client 
    :param index: the index to scan
    :param doc_type: the doc_type to scan
    :param query: the query to run
    :param routing: routing number to specific shard
    :param func: func to run on every document
    :param args: arguments at startup
    
    """
    #scroller = scan(client, query, index=index, doc_type=doc_type, routing=routing)
    #print (query)
    try:
      scroller = scan(client, query, index=index,  routing=routing)
    except Exception as error:
        print ("Error at worker, loading query (worker): "+format(error))
    for doc in scroller:
      # Call our document parser and write to Coveo Push
      func(doc, args, routing, lock, currentjson )


def _get_primary_shard(search_shards_result):
    shards = search_shards_result['shards'][0]
    return [shard for shard in shards if shard['primary'] is True][0]


def _get_nodes_to_address(shards_info):
    return dict([(k, v['transport_address'].split(':')[0]) for k, v in shards_info['nodes'].items()])
