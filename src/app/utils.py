### --------------------------------------------------------------------
### utils.py
### --------------------------------------------------------------------
### Define the arguments for the Pool applications 
### --------------------------------------------------------------------

from argparse import ArgumentParser
from elasticsearch import Elasticsearch, RequestsHttpConnection
import os
import config

# -----------------------------------------------------
# Initialize Elastic Search
# -----------------------------------------------------
def init_es(args):
    es_args = {"connection_class":RequestsHttpConnection}
    #es_args = {}
    if args.es_use_ssl:
        import certifi
        es_args = {"use_ssl": True, "verify_certs": True, "ca_certs": certifi.where()}

    return Elasticsearch([{"host": args.es_host, "port": args.es_port, "http_auth": args.es_auth}], **es_args)

# -----------------------------------------------------
# Setup the arguments for the program
# -----------------------------------------------------
def get_arg_parser():
    parser = ArgumentParser()
    parser.add_argument("-index", type=str, help="The name of the ELASTIC Search index")
    parser.add_argument("-porgid", type=str, help="The Coveo Organization ID where the Push source is defined")
    parser.add_argument("-psourceid", type=str, help="The Coveo Organization Source Id of the Push source")
    parser.add_argument("-papi", type=str, help="The Coveo Organization Push API key")

    parser.add_argument("--q", type=str, default=' {"query": {"match_all": {}}} ', help="The Query to execute in ELASTIC SEARCH (like: \"{\"query\":{\"match\": {\"source\": \"myTest\" }} })")
    parser.add_argument("--iq", type=str, default='', help="The Incremental Query to execute in ELASTIC SEARCH, refresh date [REFRESH_DATE] should be present in the query (like: \"{\"query\": { \"range\" : {  \"date\": { \"gte\": \"[REFRESH_DATE]\" }}}})")
    parser.add_argument("--id", type=str, default='', help="The date to use for the Incremental Query, normally loaded from disk. Or use like: YYYY-MM-DD ")

    #parser.add_argument("-d", "--doc-type")
    #parser.add_argument("-s", "--shard", type=int)
    parser.add_argument("-es-host", help="The Elastic search hostname (like 1baff89a12a5a0240647866b4aa95.us-east-1.aws.found.io)")
    parser.add_argument("-es-port", type=int, help="The Elastic search host port (like 9200)")
    parser.add_argument("-es-auth", help="The Elastic search username:password (like: elastic:DEWWYuu66hNZ6z7M5NMW")
    parser.add_argument("--es-use-ssl", type=bool)
    parser.add_argument("--es-direct-node", type=bool, default=False)

    return parser

# -----------------------------------------------------
# Parse the arguments
# -----------------------------------------------------
def parse_args(parser):
    args = parser.parse_args()
    #print(args)

    args.index = args.index or os.environ.get("INDEX")
    #args.doc_type = args.doc_type or os.environ.get("DOC_TYPE")
    #args.shard = args.shard or int(os.environ.get("SHARD", 0))
    args.porgid = args.porgid
    args.psourceid = args.psourceid
    args.papi = args.papi

    args.es_host = args.es_host or os.environ.get("ES_HOST")
    args.es_port = args.es_port or int(os.environ.get("ES_PORT", 9200))
    args.es_auth = args.es_auth or os.environ.get("ES_AUTH")
    
    args.es_use_ssl = args.es_use_ssl or bool(os.environ.get("ES_USE_SSL", False))
    args.es_direct_node = args.es_direct_node or bool(os.environ.get("ES_DIRECT_NODE", False))
    print(args)
    return args
