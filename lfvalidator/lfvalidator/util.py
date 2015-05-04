from md5 import md5
import json
import sys
import re
import os

conv_keys = ['source', 'title', 'created', 'comments', 'id', 'tags', 'allow_comments']
comment_keys = ['id', 'imported_display_name', 'imported_email', 'imported_url', 'author_id', 'body_html', 'created', 'parent_id', 'likes']
archive_comment_keys = ['id', 'imported_display_name','author_id', 'body_html', 'created', 'parent_id']
user_keys = ['id', 'display_name', 'tags', 'name', 'email', 'profile_url', 'settings_url', 'websites', 'location', 'bio', 'email_notifications', 'autofollow_conversations']
email_keys = ['comments', 'moderator_comments', 'moderator_flags', 'replies', 'likes']

def sanitize(filename, outfile='', is_archive=False, remove_comments=False):
    if is_archive:
        comment_keys = archive_comment_keys
    skipped_comments = 0
    skipped_convs = 0
    if not outfile:
        outfile = 'fixed_%s' % os.path.basename(filename)
    inf = open(filename)
    outf = open(outfile, 'w')
    results = open('sanitze_results.txt', 'w')
    for i, line in enumerate(inf):
        try:
            conv = json.loads(line)
        except Exception, e:
            results.write('Error on line %d: %s, here is the line:\n\n%s\n' % (i+1,e, line))
            skipped_convs += 1
            # we write out bad JSON lines anyway, just so line numbers referenced in the validator errors are consistent with the original file
            outf.write(line)
            continue
        cleaned_comments = []
        for k in conv.keys():
            if k not in conv_keys:
                conv.pop(k)
        if 'id' in conv:
            conv['id'] = str(conv['id'])
        if 'created' in conv:
            if is_archive:
                conv['created'] = conv['created'][:19] + 'Z' # double check this is always the length
            if conv['created'][-1] != 'Z' and '+' not in conv['created'] and '-' not in conv['created']:
                conv['created'] = conv['created'] + 'Z'
        if 'allow_comments' in conv:
            if conv['allow_comments'] == 'false':
                conv['allow_comments'] = False
        if remove_comments and 'comments' in conv:
            conv['is_archive'] = True
            conv['archive_count'] = len(conv['comments'])
            conv.pop('comments')
        conv['comments'] = sanitize_comments(conv, is_archive)
        outf.write(json.dumps(conv) + '\n')

    results.write('cleaned file: %s\n' % outf.name)
    results.write('skipped %d convs because bad JSON\n' % skipped_convs)
    results.write('skipped %d comments w/out a display name\n' % skipped_comments)

    for f in [inf, outf, results]:
        f.close()

    return outf.name

def sanitize_comments(conv, is_archive):
    cleaned_comments = []
    parent_ids = []
    if 'comments' not in conv:
        return []
    for comment in conv['comments']:
        for k in comment.keys():
            if k not in comment_keys:
                comment.pop(k)
        if is_archive and 'author_id' not in comment:
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
            if comment['parent_id'] == '0' or comment['parent_id'] == '' or comment['parent_id'] == 'None':
                comment.pop('parent_id')
            if is_archive and comment['parent_id'] not in parent_ids:
                comment.pop('parent_id')
        if 'id' in comment:
            comment['id'] = str(comment['id'])
        if 'created' in conv:
            if is_archive:
                comment['created'] = comment['created'][:19] + 'Z'
            if comment['created'][-1] != 'Z' and '+' not in comment['created'] and '-' not in conv['created']:
                comment['created'] = comment['created'] + 'Z'
        parent_ids.append(str(comment['id']))
        cleaned_comments.append(comment)
    return cleaned_comments

def sanitize_users(filename):
    skipped_users = 0
    inf = open(filename)
    outf = open('fixed_%s' % os.path.basename(filename), 'w')

    for i, line in enumerate(inf):
        try:
            user = json.loads(line)
        except ValueError, e:
            outf.write('Error on line %d: %s' % (i+1,e))
            skipped_users += 1
            continue
        for k in user.keys():
            if k not in user_keys:
                user.pop(k)
        user['id'] = str(user['id'])
        if user.get('email_notifications'):
            for k in user['email_notifications'].keys():
                if k not in email_keys:
                    user['email_notifications'].pop(k)
        outf.write(json.dumps(user) + '\n')

    for f in [inf, outf]:
        f.close()

    return outf.name
