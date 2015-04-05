import os
import readline

import clouseau.retention.cliutils

class Completion(object):
    '''
    user prompts, tab completion of entries
    '''
    def __init__(self, dircontents, cenv, max_depth_top_level):
        self.dircontents = dircontents
        self.cenv = cenv
        self.max_depth_top_level = max_depth_top_level
        self.choices = []
        self.choice_default = None
        self.batchno = 1  # gotta fix this sometime

    def host_completion(self, text, state):
        if text == "":
            matches = self.cenv.hostlist
        else:
            matches = [h for h in self.cenv.hostlist
                       if h.startswith(text)]
        if len(matches) > 1 and state == 0:
            for match in matches:
                print match,
            print

        try:
            return matches[state]
        except IndexError:
            return None

    def prompt_for_host(self):
        '''
        prompt user for host in hostlist,
        with tab completion
        '''
        readline.set_completer(self.host_completion)
        while True:
            host_todo = raw_input(
                "Host on which to examine dirs/files (blank to exit): ")
            host_todo = host_todo.strip()
            if host_todo == "":
                return None
            if host_todo in self.cenv.hostlist:
                return host_todo
            else:
                print "Please choose one of the following hosts:"
                clouseau.retention.cliutils.print_columns(self.cenv.hostlist, 4)

    def dir_completion(self, text, state):
        if self.cenv.cwdir is None:
            dirs_problem_to_depth = [clouseau.retention.cliutils.get_path_prefix(
                d, self.max_depth_top_level) for d in self.cenv.problem_dirs]
            dirs_skipped = [s for s in self.cenv.skipped_dirs
                            if s not in dirs_problem_to_depth]
            relevant_dirs = (sorted(list(set(dirs_problem_to_depth)))
                             + sorted(list(set(dirs_skipped))))
        else:
            self.dircontents.get(self.cenv.host, self.cenv.cwdir, self.batchno)
            relevant_dirs = sorted([s for s in self.dircontents.entries_dict
                                    if self.dircontents.entries_dict[s]['type'] == 'dir'])
        if text == "":
            matches = relevant_dirs
        else:
            depth = text.count(os.path.sep)
            # how many path elts do we have in the text, show
            # matches for basedir of it plus next elt
            matches = ([d for d in relevant_dirs
                        if d.startswith(text) and
                        d.count(os.path.sep) == depth])
        try:
            return matches[state]
        except IndexError:
            return None

    def dir_entries_completion(self, text, state):
        self.dircontents.get(self.cenv.host, self.cenv.cwdir, self.batchno)
        entries = sorted([s for s in self.dircontents.entries_dict
                          if (self.dircontents.entries_dict[s]['type'] == 'file' or
                              self.dircontents.entries_dict[s]['type'] == 'dir')])
        if text == "":
            matches = entries
        else:
            depth = text.count(os.path.sep)
            # how many path elts do we have in the text, show
            # matches for basedir of it plus next elt
            matches = ([d for d in entries
                        if d.startswith(text) and
                        d.count(os.path.sep) == depth])
        try:
            return matches[state]
        except IndexError:
            return None

    def prompt_for_dir(self):
        '''
        prompt user for host in self.hostlist,
        with tab completion
        '''

        readline.set_completer(self.dir_completion)
        dir_todo = raw_input("Directory (blank to exit): ")
        dir_todo = dir_todo.strip()
        if dir_todo == "":
            return None
        else:
            return dir_todo

    def set_choices_completion(self, choices, default):
        self.choices = choices
        self.choice_default = default
        readline.set_completer(self.choices_completion)

    def choices_completion(self, text, state):
        matches = self.choices
        if text == "":
            matches = [self.choice_default]
        try:
            return matches[state]
        except IndexError:
            return None
