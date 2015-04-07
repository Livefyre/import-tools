from util import sanitize
from jsonschema import Draft4Validator, validate
from jsonschema.exceptions import ValidationError
from collections import defaultdict
import json
import requests
import re
import sys
import time
import hashlib

error_msg = {'body_html': 'has malformed content: ', 'source': 'is not a properly formed URL', 'title': 'cannot have HTML entities', 'created': 'is not a ISO8601 timestamp', 'imported_email': 'is not a properly formed email address', 'imported_url': 'is not a valid url', 'likes': 'likes cannot contain duplicate values', 'tags': 'tags cannot contain duplicate values'}
error_summary = {'required': 'missing a required field', 'type': 'an incorrect type for a field', 'pattern': 'improperly formated timestamp, url, or email address', 'not': 'malformed content in a comment body', 'uniqueItems': 'duplicate author ID values for likes', 'maxLength': 'longer than maximum length', 'minLength': 'shorter than minimum length'}
invalid_tags = re.compile(r'(?=<(?!/?(?:img(?:\s+src\s*=\s*(?:"[^"]*"|\'[^\']*\')\s*)|a(?:\s+(?:href|target)\s*=\s*(?:"[^"]*"|\'[^\']*\')\s*){0,2}|a|img|span|label|p|br|br/|strong|em|u|blockquote|ul|li|ol|pre|body|b|i)>))</?[^>]+>')
first_word = re.compile(r'^.{2}([^\']+).(.*)$')
new_lines = re.compile(r'\n')
escaped_angle_brackets = re.compile(r'&lt;[^&]*&gt;')

critical_flags = {
    'has_bad_tags': False,
    'has_bad_brackets': False,
    'has_bad_newlines': False
}

critical_error_msgs = {'has_bad_tags': 'Your file has invalid HTML tags. Please check http://answers.livefyre.com/developers/imports/comment-import/ to see what tags are allowed. All invalid tags will not be imported correctly.',
    'has_bad_brackets': 'Your file has encoded angle brackets in comment bodies. Any HTML tags in comments do not need to be HTML escaped; they should appear as "<p>", not "%lt;p%gt;". If they are encoded they will not be interpreted correctly and will be printed verbatim.',
    'has_bad_newlines': 'Your file has newlines characters "\\n" which will not be interpreted correctly. Line breaks must be represented as either "</p><p>"" or "<br>". Any "\\n" values will be printed verbatim.'
}

def validate(infile, outfile='validator_results.txt'):
    start = time.time()
    cleaned_file = sanitize(infile)
    inf = open(cleaned_file)
    outf = open(outfile, 'w')

    r = requests.get('https://raw.githubusercontent.com/Livefyre/integration-tools/master/lfvalidator/jsonschema/conv_schema.json')
    schema = json.loads(r.text)

    counter = defaultdict(int)
    count = 0

    for l in inf:
        count += 1
        try:
            j = json.loads(l)
            l = unicode(l)
            v = Draft4Validator(schema)
            errors = sorted(v.iter_errors(j), key=lambda e: e.path)
            if not errors:
                continue
            print '\nErrors on line %d:' % count
            outf.write('\nErrors on line %d:\n' % count )
            for error in errors:
                print_error(error, j, outf, counter)
        except Exception, e:
            print e
            print '\nError, bad JSON on line %d' % count
            outf.write('\nError, bad JSON on line %d\n' % count)
            counter['unicode'] += 1
            continue
    end = time.time()
    delta = end - start

    print '\nError summary:'
    print_summary(counter)
    print_critical_errors()

    print '\nFile has %d total errors' % sum(counter.values())
    outf.write('\nFile has %d total errors\n' % sum(counter.values()))
    print '%d lines processed in %s seconds' % (count, delta)
    outf.write('%d lines processed in %s seconds\n' % (count, delta))
    
    inf.close()
    generate_receipt(outfile, outf)
    outf.close()

def print_summary(counter):
    for k,v in counter.iteritems():
        try:
            keys = k.split(',')
            reason, field = error_summary[keys[0]], keys[1]
            print '%d errors were due to %s on field %s' % (v, reason, field)
        except KeyError:  #this has problems, could be due to print error
            print '%d errors were due to invalid JSON' % v

def print_critical_errors():
    print '\nCritical issues:'
    critical_errors = [k for k,v in critical_flags.iteritems() if v == True]
    for g in critical_errors:
        print critical_error_msgs[g]

def print_error(error, line, outf, counter):
    if error.validator == 'type':
        if error.path[-1] is int:
            # pop off index of bad likes value
            error.path.pop()
        key = error.path.pop()
        msg = '%s value %s is not of type %s' % (key, str(error.instance), error.validator_value)
        # what is left is ['comments', 0]
    elif error.validator == 'required':
        group = first_word.match(error.message).groups()
        key = group[0]
        # handles if they are missing a required field
        msg = key + group[1]
    elif error.validator in ('maxLength', 'minLength'):
        key = error.path.pop()
        msg = '%s value violates %s rule' % (key, error.validator)
    else:
        try:
            # the rest all follow the same pattern
            key = error.path.pop()
            msg = '%s %s' %  (key, error_msg[key])
            if key == 'body_html':
                bad_tags = invalid_tags.findall(line['comments'][error.path[1]]['body_html'])
                bad_newlines = new_lines.findall(line['comments'][error.path[1]]['body_html'])
                bad_newlines = ['\\n' if x == '\n' else x for x in bad_newlines]
                bad_brackets = escaped_angle_brackets.findall(line['comments'][error.path[1]]['body_html'])
                bad_dict = {'Bad HTML tags': bad_tags, 'Bad line breaks': bad_newlines, 'Encoded angle brackets': bad_brackets}
                for k,v in bad_dict.items():
                    set_critical_messages(bad_dict)
                    if v:
                        msg += '\n%s: ' % k + ', '.join(v)
        except Exception,e:
            print 'No key for error \"%s\"' % e
    if error.path:
        msg += ' in comment with ID %s' % str(line['comments'][error.path.pop()]['id'])
    print msg.encode('utf8')
    outf.write(msg.encode('utf8') + '\n')
    k = error.validator + ',' + key
    counter[k] += 1

def set_critical_messages(errors_dict):
    vals_to_check = [k for k,v in critical_flags.iteritems() if v == False]
    for _ in vals_to_check:
        if errors_dict['Bad HTML tags']:
            critical_flags['has_bad_tags'] = True
        if errors_dict['Bad line breaks']:
            critical_flags['has_bad_newlines'] = True
        if errors_dict['Encoded angle brackets']:
            critical_flags['has_bad_brackets'] = True

def generate_receipt(filename, outf):
    receipt = open('receipt.txt', 'w')
    md5 = hashlib.md5()
    with open(filename,'rb') as f: 
        for chunk in iter(lambda: f.read(8192), b''): 
            md5.update(chunk)
    md5string = md5.hexdigest()
    receipt.write('%s' % md5string)
    print '\nHERE IS YOUR RECEIPT: %s' % md5string
    outf.write('\nHERE IS YOUR RECEIPT: %s' % md5string)

def main():
    args = sys.argv[1:]
    if len(args) not in (1,2,3):
        print 'Usage: python import_validator.py [input file] [~optional schema file] [~optional output file]'
        sys.exit(0)
    validate(*args)

if __name__ == '__main__':
    main()
