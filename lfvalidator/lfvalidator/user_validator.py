from util import sanitize_users
from prune import prune_users
from jsonschema import Draft4Validator, validate
from jsonschema.exceptions import ValidationError
from collections import defaultdict
import json
import requests
import re
import sys
import time
import hashlib

def validate_users(comment_file, user_file, skip_prune=False, outfile='user_validator_results.txt'):
    sanitized_user_file = sanitize_users(user_file)
    if not skip_prune:
        pruned_user_file = prune_users(comment_file, sanitized_user_file)
    else:
        pruned_user_file = sanitized_user_file
    outf = open(outfile, 'w')
    timestamp = str(int(time.time()))
    r = requests.get('https://raw.githubusercontent.com/Livefyre/integration-tools/master/lfvalidator/jsonschema/user_schema.json?%s' % timestamp)
    schema = json.loads(r.text)

    author_ids = []
    counter = defaultdict(int)
    validator = Draft4Validator(schema)
    start = time.time()

    with open(pruned_user_file) as inf:
        for i,l in enumerate(inf):
            try:
                j = json.loads(l)
                errors = sorted(validator.iter_errors(j), key=lambda e: e.path)
                if not errors:
                    continue
                print '\nErrors on line %d:' % (i+1)
                outf.write('\nErrors on line %d:\n' % (i+1))
                if j['id'] in author_ids:
                    print 'Duplicate id field for collection id %s.' % j['id']
                author_ids.append(j['id'])
                for error in errors:
                    # print_error(error, j, outf, counter)
                    print error
            except ValueError, e:
                print '\nError, bad JSON on line %d' % (i+1)
                outf.write('\nError, bad JSON on line %d\n' % (i+1))
                continue
            except:
                continue

    end = time.time()
    delta = end - start

    # print '\nFile has %d total errors' % sum(counter.values())
    # outf.write('\nFile has %d total errors\n' % sum(counter.values()))
    # print '%d lines processed in %s seconds' % (i+1, delta)
    # outf.write('%d lines processed in %s seconds\n' % (count, delta))
    outf.close()

def main():
    args = sys.argv[1:]
    if len(args) not in (1,2,3,4):
        print 'Usage: python user_validator.py [comment file] [user file] [~optional skip user prune] [~optional output file]'
        sys.exit(0)
    validate_users(*args)

if __name__ == '__main__':
    main()
