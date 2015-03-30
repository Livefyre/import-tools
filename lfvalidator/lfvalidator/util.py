from md5 import md5
import json
import sys
import re
import os

conv_keys = ['source', 'title', 'created', 'comments', 'id', 'tags', 'allow_comments']
comment_keys = ['id', 'imported_display_name', 'imported_email', 'imported_url', 'author_id', 'body_html', 'created', 'parent_id', 'likes']

def sanitize(filename, archive=False):
    skipped_comments = 0
    skipped_convs = 0
    inf = open(filename)
    outf = open('fixed_%s' % os.path.basename(filename), 'w')
    results = open('sanitze_results.txt', 'w')

    for i, line in enumerate(inf):
        try:
            conv = json.loads(line)
        except Exception, e:
            outf.write('Error on line %d: %s' % (i+1,e))
            skipped_convs += 1
            continue
        cleaned_comments = []
        for k in conv.keys():
            if k not in conv_keys:
                conv.pop(k)
        conv['id'] = str(conv['id'])
        if conv['created'][-1] != 'Z' and '+' not in conv['created']:
            conv['created'] = conv['created'] + 'Z'
        if not conv['comments']:
            continue
        for comment in conv['comments']:
            for k in comment.keys():
                if k not in comment_keys:
                    comment.pop(k)
            if archive and 'author_id' not in comment:
                try:
                    clean_display_name = re.sub(r'[^\x00-\x7F]+',' ', comment['imported_display_name'])
                    comment['author_id'] = md5(clean_display_name).hexdigest()
                except Exception, e:
                    outf.write('%s' % e)
                    skipped_comments += 1
                    continue
            if 'author_id' in comment:
                comment['author_id'] = str(comment['author_id'])
            if 'parent_id' in comment:
                comment['parent_id'] = str(comment['parent_id'])
                if comment['parent_id'] == "0" or comment['parent_id'] == "" or comment['parent_id'] == 'None':
                    comment.pop('parent_id')
            comment['id'] = str(comment['id'])
            if comment['created'][-1] != 'Z' and '+' not in comment['created']:
                comment['created'] = comment['created'] + 'Z'
            cleaned_comments.append(comment)
        conv.pop('comments')
        conv['comments'] = cleaned_comments
        outf.write(json.dumps(conv) + '\n')

    results.write('cleaned file: %s\n' % outf.name)
    results.write('skipped %d convs because bad JSON\n' % skipped_convs)
    results.write('skipped %d comments w/out a display name\n' % skipped_comments)

    for f in [inf, outf, results]:
        f.close()

    return outf.name
