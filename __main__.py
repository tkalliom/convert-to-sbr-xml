import argparse
from uuid import uuid4
from time import strftime, localtime

from parsers.factory import get_parser
from sbr.elements import Smses, Calls
from sbr.utils import format_current_time
from tree.xml_serialization import serialize

file_timestamp = strftime("%Y%m%d%H%M%S", localtime()) # when the export was started, local time

handler = argparse.ArgumentParser()
handler.add_argument('infile', nargs='+')
handler.add_argument('--type', '-t', choices=['smses', 'calls'])

args = handler.parse_args()

smscollection = None if (args.type == 'calls') else Smses()
callcollection = None if (args.type == 'smses') else Calls()

for infilename in args.infile:
  parser = get_parser(infilename)
  with open(infilename, 'rb') as infile:
    parser.parse(infile, sms_list=smscollection, call_list = callcollection)

collection_timestamp = format_current_time() # when the export was finished, Unix timestamp (milliseconds)
uuid = uuid4()

for collection in [smscollection, callcollection]:
  if collection:
    collection['backup_date'] = collection_timestamp
    collection['backup_set'] = uuid
    collection.sort()
    with open(collection.filename_prefix() + file_timestamp + ".xml", 'wb') as outfile:
      xmlstring = serialize(collection)
      outfile.write(xmlstring)
