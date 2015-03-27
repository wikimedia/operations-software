import os
import sys
import readline
import atexit

sys.path.append('/srv/audits/retention/scripts/')

import retention.remotefileauditor
import retention.utils
import retention.fileutils
import retention.ruleutils


def init_readline_hist():
    readline.parse_and_bind("tab: complete")
    histfile = os.path.join(os.path.expanduser("~"), ".audit_hist")
    try:
        readline.read_history_file(histfile)
    except IOError:
        pass
    atexit.register(readline.write_history_file, histfile)
    # also fix up delims so we don't have annoying dir elt behavior
    delims = readline.get_completer_delims()
    delims = delims.replace("/", "")
    readline.set_completer_delims(delims)

def save_history(histfile):
    readline.write_history_file(histfile)

def get_path_prefix(path, depth):
    if path is None:
        return path
    if path.count(os.path.sep) < depth:
        return path
    fields = path.split(os.path.sep)
    return os.path.sep.join(fields[:depth + 1])

def print_columns(items, cols):
    num_rows = len(items) / cols
    extra = len(items) % cols
    if extra:
        num_rows = num_rows + 1

    max_len = {}
    for col in range(0, cols):
        max_len[col] = 0

    for row in range(0, num_rows):
        for col in range(0, cols):
            try:
                text = items[row + num_rows * col]
            except IndexError:
                continue
            try:
                count = len(unicode(text, 'utf-8'))
            except:
                count = len(text)
            if len(text) > max_len[col]:
                max_len[col] = len(text)

    for row in range(0, num_rows):
        for col in range(0, cols):
            try:
                # fixme ljust probably gets this wrong for
                # text that's really multibyte chars
                print items[row + num_rows * col].ljust(max_len[col]),
            except IndexError:
                pass
        print

def show_help(level):
    if level == 'status':
        print """Status must be one of the following:
        P  (the directory or file may contain sensitive information)
        G  (the directory or file is known to be ok and should remain so)
        R  (the directory or file is known to be ok but entries
        must be rechecked on next run)
        U  (the file or directory has not been checked, status unknown)
        Q  (quit this level of the menu)"""
    elif level == 'top':
        print """Command must be one of the following:
        S  set the status for the directory
        E  examine the directory
        F set filter for listing directory contents
        I  ignore this directory or file for now
        R  show rules for all dirs/files
        Q  quit the menu"""
    elif level == 'examine':
        print """Command must be one of the following:
        D descend the directory tree one level (user will be prompted for subdir)
        U ascend the directory tree one level (not higher than base of tree)
        E show information on entries in directory
        F set filter for listing directory contents
        C show first few lines of contents of file in directory
        R  show rules covering current directory
        M  mark file(s) as ok (user will be prompted for filename expr)
        Q  quit the menu"""
    elif level == 'rule':
        print """Command must be one of the following:
        S show all rules for this host
        D show all rules covering the current directory
        C show all rules covering current directory contents
        A add rule to rules store
        R remove rule from rules store
        I import rules from file (overrides dups, won't remove other rules)
        E export rules to file
        Q quit the menu"""
    else:
        print "unknown help level requested,", level

def show_pager(current_page, num_items, num_per_page):
    readline.set_completer(None)
    while True:
        to_show = raw_input("P(prev)/N(next)/F(first)/"
                            "L(last)/<num>(go to page num)/Q(quit) [N]: ")
        to_show = to_show.strip()
        if to_show == "":
            to_show = 'N'

        if to_show == 'P' or to_show == 'p':
            # prev page
            if current_page > 1:
                return current_page - 1
            else:
                return current_page

        elif to_show == 'N' or to_show == 'n':
            # next page
            num_pages = num_items / num_per_page
            if num_items % num_per_page:
                num_pages += 1
            if current_page < num_pages:
                return current_page + 1
            else:
                return current_page

        elif to_show == 'F' or to_show == 'f':
            # first page
            return 1

        elif to_show == 'L' or 'to_show' == 'l':
            # last page
            num_pages = num_items / num_per_page
            if num_items % num_per_page:
                num_pages += 1
            return num_pages

        elif to_show.isdigit():
            desired_page = int(to_show)
            num_pages = num_items / num_per_page
            if num_items % num_per_page:
                num_pages += 1

            if desired_page < 1:
                return 1
            elif desired_page > num_pages:
                return num_pages
            else:
                return desired_page

        elif to_show == 'Q' or to_show == 'q':
            return None
        else:
            print "unknown option"

def check_rules_path(rules_path):
    # sanity check on the path, let's not read/write
    # into/from anything in the world

    # fixme write this
    return True

