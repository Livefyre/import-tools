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
import os

error_msg = {'body_html': 'has malformed content: ', 'source': 'is not a properly formed URL', 'title': 'cannot have HTML entities', 'created': 'is not a ISO8601 timestamp', 'imported_email': 'is not a properly formed email address', 'imported_url': 'is not a valid url', 'likes': 'likes cannot contain duplicate values', 'tags': 'tags cannot contain duplicate values'}
error_summary = {'required': 'missing a required field', 'type': 'an incorrect type for a field', 'pattern': 'improperly formated timestamp, url, or email address', 'anyOf': 'improperly formated timestamp, url, or email address', 'not': 'malformed content in a comment body', 'uniqueItems': 'duplicate author ID values for likes', 'maxLength': 'longer than maximum length', 'minLength': 'shorter than minimum length', 'invalid': 'non-existent parent ID', 'duplicate comment': 'duplicate comment id values', 'duplicate conv': 'duplicate collection id values'}
invalid_tags = re.compile(r'(?=<(?!/?(?:img(?:\s+src\s*=\s*(?:"[^"]*"|\'[^\']*\')\s*)|a(?:\s+(?:href|target)\s*=\s*(?:"[^"]*"|\'[^\']*\')\s*){0,2}|a|img|span|label|p|br|br/|strong|em|u|blockquote|ul|li|ol|pre|body|b|i)>))</?[^>]+>')
first_word = re.compile(r'^.{2}([^\']+).(.*)$')
new_lines = re.compile(r'\n')
escaped_angle_brackets = re.compile(r'&lt;[^&]*&gt;')
double_backslash = re.compile(r'\\[^\s]*')

critical_error_map = {
    'Bad HTML tags': 'has_bad_tags',
    'Bad line breaks': 'has_bad_newlines',
    'Encoded angle brackets': 'has_bad_brackets',
    'Escaped backslashes': 'has_bad_backslashes'
}

critical_flags = {
    'has_bad_tags': False,
    'has_bad_brackets': False,
    'has_bad_newlines': False,
    'has_bad_backslashes': False,
}

critical_error_msgs = {'has_bad_tags': 'Your file has invalid HTML tags. Please check http://answers.livefyre.com/developers/imports/comment-import/ to see what tags are allowed. All invalid tags will be parsed out.',
    'has_bad_brackets': 'Your file has encoded angle brackets in comment bodies. Any HTML tags in comments do not need to be HTML escaped; they should appear as "<p>", not "&lt;p&gt;". If they are encoded they will not be interpreted correctly and will be printed verbatim.',
    'has_bad_newlines': 'Your file has newlines characters "\\n" which will not be interpreted correctly. Line breaks must be represented as either "</p><p>"" or "<br>". Any "\\n" values will be printed verbatim.',
    'has_bad_backslashes': 'Your file has escaped (double) backslashes. Escaped backslashes will be interpretted as a literal backslash. If this is not what you want, please use single backslashes for special encodings.'
}

def validate(infile, outfile='validator_results.txt', is_archive=False):
    start = time.time()
    if is_archive:
        archive_filename = 'archive_' + os.path.basename(infile)
        sanitize(infile, archive_filename, True, True)
    cleaned_file = sanitize(infile, '', is_archive, False)
    inf = open(cleaned_file)
    outf = open(outfile, 'w')
    timestamp = str(int(time.time()))

    r = requests.get('https://raw.githubusercontent.com/Livefyre/integration-tools/master/lfvalidator/jsonschema/conv_schema.json?%s' % timestamp)
    schema = json.loads(r.text)

    counter = defaultdict(int)
    count = 0
    conv_ids = []
    validator = Draft4Validator(schema)

    for i,l in enumerate(inf):
        try:
            j = json.loads(l)
            errors = sorted(validator.iter_errors(j), key=lambda e: e.path)
            if not errors:
                continue
            print '\nErrors on line %d:' % (i+1)
            outf.write('\nErrors on line %d:\n' % (i+1))
            if j['id'] in conv_ids:
                print 'Duplicate id field for collection id %s' % j['id']
                outf.write('Duplicate id field for collection id %s\n' % j['id'])
                k = 'duplicate conv,id'
                counter[k] += 1
            conv_ids.append(j['id'])
            for error in errors:
                print_error(error, j, outf, counter)
            check_parent_ids(j, counter, outf)
        except ValueError, e:
            print '\nError, bad JSON on line %d' % (i+1)
            outf.write('\nError, bad JSON on line %d\n' % (i+1))
            counter['bad json,'] += 1
            continue
        except:
            continue
    end = time.time()
    delta = end - start

    
    print_summary(counter, outf)
    print_critical_errors(outf)

    print '\nFile has %d total errors' % sum(counter.values())
    outf.write('\nFile has %d total errors\n' % sum(counter.values()))
    print '%d lines processed in %s seconds' % (i+1, delta)
    outf.write('%d lines processed in %s seconds\n' % (i+1, delta))
    
    inf.close()
    # generate_receipt(outfile, outf)
    outf.close()

def print_summary(counter, outf):
    print '\nError summary:'
    outf.write('\nError summary:\n')
    for k,v in counter.iteritems():
        try:
            keys = k.split(',')
            if keys[0] == 'bad json':
                print '%d errors were due to invalid JSON' % v
                outf.write('%d errors were due to invalid JSON\n' % v)
            reason, field = error_summary[keys[0]], keys[1]
            print '%d errors were due to %s on field %s' % (v, reason, field)
            outf.write('%d errors were due to %s on field %s\n' % (v, reason, field))
        except:
            continue

def print_critical_errors(outf):
    print '\nCritical issues:'
    outf.write('\nCritical issues:\n')
    critical_errors = [k for k,v in critical_flags.iteritems() if v == True]
    for g in critical_errors:
        print critical_error_msgs[g]
        outf.write('%s\n' % critical_error_msgs[g])

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
                body_val = line['comments'][error.path[1]]['body_html']
                bad_tags = invalid_tags.findall(body_val)
                bad_newlines = new_lines.findall(body_val)
                bad_newlines = ['\\n' if x == '\n' else x for x in bad_newlines]
                bad_brackets = escaped_angle_brackets.findall(body_val)
                # bad_backslashes = double_backslash.findall(body_val)
                # bad_backslashes = [s.replace('\\', '\\\\') for s in bad_backslashes]
                bad_backslashes = [] # take out double backslash check for now
                bad_dict = {'Bad HTML tags': bad_tags, 'Bad line breaks': bad_newlines, 'Encoded angle brackets': bad_brackets, 'Escaped backslashes': bad_backslashes}
                for k,v in bad_dict.items():
                    if v:
                        msg += '\n%s: ' % k + ', '.join(v)
                set_critical_messages(bad_dict)
        except Exception,e:
            print 'No key for error \"%s\"' % e
    if error.path:
        msg += ' in comment with ID %s' % str(line['comments'][error.path.pop()]['id'])
    print msg.encode('utf8')
    outf.write(msg.encode('utf8') + '\n')
    k = error.validator + ',' + key
    counter[k] += 1

def set_critical_messages(errors_dict):
    vals_to_check = [critical_error_map[k] for k,v in errors_dict.iteritems() if len(v)]
    for k in vals_to_check:
        critical_flags[k] = True

def check_parent_ids(conv, counter, outf):
    if not conv['comments']:
        return
    parent_ids = []
    comment_ids = []
    for comment in conv['comments']:
        parent_ids.append(comment['id'])
        if comment['id'] in comment_ids:
            print 'Duplicate id field for comment id %s' % comment['id']
            outf.write('Duplicate id field for comment id %s\n' % comment['id'])
            k = 'duplicate comment,id'
            counter[k] += 1
        comment_ids.append(comment['id'])
        parent_id = comment.get('parent_id')
        if parent_id:
            if parent_id not in parent_ids:
                print 'Comment with id %s refers to non-existent parent_id %s' % (comment['id'], parent_id)
                outf.write('Comment with id %s refers to non-existent parent_id %s\n' % (comment['id'], parent_id))
                k = 'invalid,parent_id'
                counter[k] += 1


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
        print 'Usage: python import_validator.py [input file] [~optional output file]'
        sys.exit(0)
    validate(*args)

if __name__ == '__main__':
    main()
