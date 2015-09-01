import json
import sys
from subprocess import check_output as cmd

def prune_users(comment_file, user_file): 
    commenters_set = set()
    comment_file = open(comment_file, 'r')
    full_user_file = open(user_file, 'r')
     
    comment_errors = 0
    user_errors = 0
    authors_matched = 0

    pruned_user_file = open('Users_Reduced.json', 'w')
    errors_file = open('Errors.txt', 'w')

    for line in comment_file:
        try:
            conv = json.loads(line)
            for comment in conv['comments']:
                commenters_set.add(str(comment.get('author_id')))
        except Exception as e:
            comment_errors += 1
            errors_file.write(str(e) + '\n')
            errors_file.write(line)
            pass

    total_users = len(commenters_set)
    for user_line in full_user_file:
        try:
            user = json.loads(user_line)
            if str(user['id']) in commenters_set:
                pruned_user_file.write(user_line)
                commenters_set.remove(str(user['id']))
                authors_matched += 1
        except Exception as e:
            errors_file.write(str(e) + '\n')
            errors_file.write(user_line)
            user_errors += 1
            pass

    print '%d users matched out of %d total users\n' % (authors_matched, total_users)
    errors_file.write('%d users matched out of %d total users\n' % (authors_matched, total_users))
    errors_file.write('Comment errors: ' + str(comment_errors) + '\n')
    errors_file.write('User errors: ' + str(user_errors) + '\n')
     
    for f in [comment_file, full_user_file, pruned_user_file, errors_file]:
        f.close()

    cmd(['rm', '-rf', user_file])

    return pruned_user_file.name
