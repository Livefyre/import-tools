#https://github.com/Julian/jsonschema

from jsonschema import validate
import json
import requests
import sys

if len(sys.argv) > 1:
    f = open(sys.argv[1], "r")
else:
    sys.exit("Please specify conv.json file to validate")

r = requests.get('https://github.com/Livefyre/integration-tools/raw/master/import-validator/jsonschema/conv_schema.json')
schema = json.loads(r.text)

for l in f.readlines():
    j = json.loads(l)
    print validate(j, schema)