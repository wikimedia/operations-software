import os
import re
import smtplib
import email.mime.text
import glob
import getopt
import sys
import time
import traceback


class AuditScanner(object):
    '''
    scan lines of audit report output
    '''

    @staticmethod
    def merge_entries(old_entries, new_entries):
        '''
        given two holders of entries, merge
        the second into the first and return it
        '''

        if new_entries is not None:
            for host in new_entries:
                if host not in old_entries:
                    old_entries[host] = new_entries[host]
                else:
                    for user in new_entries[host]:
                        if user not in old_entries[host]:
                            old_entries[host][user] = new_entries[host][user]
                        else:
                            old_entries[host][user].extend(
                                new_entries[host][user])
        return old_entries

    @staticmethod
    def get_user_from_entry(entry):
        '''
        get username from an audit report line
        and return it; the line should have
        the full path of the entry first in the line;
        we expect paths like /home/someuser/blah/blah...
        '''

        try:
            user = entry.split('/')[2]
        except:
            return None

        return user

    def __init__(self, hosts, users):
        '''
        hosts is a list of hostnames (basename only)
        for which entries will be collected; if None, all
        hosts in the audit output will be processed

        users is a comma separated string of usernames
        as they appear in home directory paths, for which
        entries will be collected; if None, all users
        in the audit output will be processed
        '''

        self.users = users
        self.hosts_todo = hosts

        self.host = None
        self.entries = {}

    def setup(self, line):
        '''
        get hostname from the audit report line passed in,
        stash it, initialize the holder for that hosts's entries
        '''

        self.host = line[6:].strip().split('.')[0]
        if self.hosts_todo is None or self.host in self.hosts_todo:
            if self.host not in self.entries:
                self.entries[self.host] = {}
        else:
            # skip this host
            self.host = None

    def stash_entry(self, entry):
        '''
        given an entry name (a file path),
        dig the username out of the path and
        stash the entry in the holder for that user's
        entries
        '''

        if entry is None:
            return True   # no entry, no error.

        user = AuditScanner.get_user_from_entry(entry)
        if user is None:
            return False  # error

        if self.users is None or user in self.users:
            if user not in self.entries[self.host]:
                self.entries[self.host][user] = []
            self.entries[self.host][user].append(entry)
        return True

    def get_entries(self):
        '''
        call send(None) once to set up this function
        to run

        then pass audit report lines into it
        with send(); when all lines have been passed
        in, reference the entries holder of the instance
        to get the results
        '''

        while self.host is None:
            line = yield
            if line is None:
                yield True  # error
            elif line.startswith('host: '):
                self.setup(line)
                break
            # in all other cases ignore the line

        line = yield
        while line is not None:
            error = False
            entry = None
            if line.startswith('host: '):
                self.setup(line)
            elif self.host is None:
                # host being skipped
                pass
            elif line.startswith('#') or not line.strip():
                # comments, whitespace are skipped
                pass
            elif line.startswith(AuditEmailer.warning_text):
                entry = line[AuditEmailer.len_warning_text:].strip()
            elif line.startswith('WARNING:') or line.startswith('INFO:'):
                # warning/info lines without entries are skipped
                pass
            else:
                result = AuditEmailer.entryname_pattern.match(line)
                if result is not None:
                    entry = result.group(1)
                else:
                    error = True

            if not error:
                error = not self.stash_entry(entry)
            line = yield error

        raise StopIteration


class AuditEmailer(object):
    '''
    read audit output, transform it into emails, send them
    '''

    warning_text = 'WARNING: too many files to audit in directory '
    len_warning_text = len(warning_text)
    # file:/home/wikipedia/syslog/archive/syslog-20140817.gz     owner:0
    #   creat:Sun Aug 17 07:59:37 2014 mod:Sun Aug 17 06:45:35 2014
    #   open:F empty:F old:F type gzip compressed data, from Unix,
    #   last modified: Sun Aug 17 07:57:30 2014
    entryname_pattern = re.compile(r'^file:(/.+)\s*owner:[0-9]+\s+creat:.*\s'
                                   r'+mod:.*\s+open:[TF]\s+empty:[TF-]\s'
                                   r'+old:[TF-]\s+type:.*$')
    email_form_text = (
        """Dear WMF Colleague,

This is the result of the latest data retention audit.

Please check and remove any files and directories in the list
below that contain sensitive data and are older than 90 days.
If files or directories appear in this list in error, you can
add them to the file ".data_retention" in your home directory.
This file should have one filename or directory (full path
always) per line, with directories ending in '/' to distinguish
them from files.  Lines starting with '#' or blank lines are
skipped.

Thanks and happy cleanup,

Your friendly data auditor script.

---------------------------------------------------------------

"""
    )

    def __init__(self, email_addrs_file, audit_output_dir, mail_from,
                 mail_subject, mail_server, formmail,
                 users, hosts, to_default, verbose, dryrun):
        self.email_addrs_file = email_addrs_file
        self.audit_output_dir = audit_output_dir
        self.mail_from = mail_from
        self.mail_subject = mail_subject
        self.mail_server = mail_server
        self.homes_vs_addrs = {}
        self.formmail = formmail
        self.users = users
        self.hosts = hosts
        self.to_default = to_default
        self.verbose = verbose
        self.dryrun = dryrun

        if self.formmail:
            self.form_mail_text = open(formmail).read()
        else:
            self.form_mail_text = AuditEmailer.email_form_text

    def get_homes_emails(self):
        '''
        get dict of home dir names vs user emails from
        file mapping home dirs to emails

        lines in file should have the user home dir followed
        by the email address, with spaces separating the two
        fields.  Example:
        ariel    ariel@wikimedia.org

        lines without '@' wil be skipped.
        '''

        homes_vs_addrs = {}
        content = open(self.email_addrs_file, "r").read()
        lines = content.split("\n")
        for line in lines:
            line = line.strip()
            if '@' not in line:
                continue
            fields = line.split()
            homes_vs_addrs[fields[0]] = fields[1]
        return homes_vs_addrs

    def get_email_text(self, entries_per_user):
        '''
        given dict of all audited entries by host/user,
        generate and return the approriate email text
        '''

        emails = {}
        for host in sorted(entries_per_user.keys()):
            for user in entries_per_user[host]:
                if not len(entries_per_user[host][user]):
                    if self.verbose:
                        print "skipping user", user, "because no entries"
                    continue
                if user not in emails:
                    if self.verbose:
                        print "will send email to", user
                    emails[user] = self.form_mail_text
                emails[user] += "Host: %s\nFiles:\n" % host
                for entry in entries_per_user[host][user]:
                    emails[user] += entry + "\n"
                emails[user] += "\n"
        return emails

    def send_emails(self, email_texts):
        '''
        given email texts for each user, get the
        user email address and send the email
        '''

        for user in email_texts:
            if user not in self.homes_vs_addrs:
                if self.to_default is not None:
                    user_address = self.to_default
                    print "Falling back to %s for user %s" % (self.to_default, user)
                else:
                    print "Can't find user '%s', skipping" % user
                    continue
            else:
                user_address = self.homes_vs_addrs[user]

            message = email.mime.text.MIMEText(email_texts[user])
            message["Subject"] = self.mail_subject
            message["From"] = self.mail_from
            message["To"] = user_address

            if self.dryrun:
                print message
            else:
                try:
                    server = smtplib.SMTP(self.mail_server)
                    server.sendmail(self.mail_from, user_address,
                                    message.as_string())
                    server.close()
                except:
                    print 'problem sending mail to', user_address
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    except_message = repr(traceback.format_exception(
                        exc_type, exc_value, exc_traceback))
                    print except_message
            time.sleep(1)

    def run(self):
        '''
        do all the work
        '''

        self.homes_vs_addrs = self.get_homes_emails()
        if self.verbose:
            print 'email addresses retrieved'

        if self.users:
            users = self.users.split(',')
            if self.verbose:
                print "emailing only these users:", self.users
        else:
            users = None

        if self.hosts:
            hosts = [h.split('.')[0] for h in self.hosts.split(',')]
            if self.verbose:
                print "only processing output from these hosts:", hosts
        else:
            hosts = None

        entries_per_user = {}

        for filename in glob.glob(os.path.join(self.audit_output_dir,
                                               "*final.txt")):

            if self.verbose:
                print 'doing file:', filename

            content = open(filename, 'r').read()
            entries = content.split('\n')

            scanner = AuditScanner(hosts, users)
            retriever = scanner.get_entries()
            retriever.send(None)
            for line in entries:
                error = retriever.send(line)
                if error:
                    print "Problem with file", filename, "line", line

            result = scanner.entries
            entries_per_user = AuditScanner.merge_entries(
                entries_per_user, result)

        emails = self.get_email_text(entries_per_user)
        if self.verbose:
            if emails:
                print 'email texts ready, sending'
            else:
                print 'no emails to send, done'

        self.send_emails(emails)


def usage(message=None):
    '''
    display an optional mssage and usage information
    '''

    if message:
        sys.stderr.write(message + "\n")
    usage_message = """Usage: do_audit_emails.py --mailserver <hostname>
             [--auditdir <path>] [--subject <text>] [--fromaddr <addr>]
             [--emailadddrs] [--users username[,username...]]
             [--hosts hostname[,hostname...]] [--todefault <addr>]
             [--dryrun]

This script reads output from a data retention audit and generates and
sends mails to user with the files an diretories located by the audit as
possibly a problem.

Options:

  --mailserver (-m)  fqdn of mail server
  --auditdir   (-d)  directory containing the audit outputs
                     (default: audit_dir_YYYYMMDD)
                     files within this directory generated
                     by data_auditor.py run remotely via salt
                     and ending in "final.txt" will be
                     scanned, everything else will be ignored
  --subject    (-s)  subject of emails to be sent (default:
                     'Data retention audit')
  --fromaddr   (-f)  email address to use for From:
                     (default: data_auditor@wikimedia.org)
  --emailaddrs (-a)  file mapping home dirs to email addrs
                     (default: homes_vs_addresses.txt)
  --formmail   (-F): name of file with form mail text
                     (default: use hardcoded text in script)
  --users      (-u)  only generate and send emails for the
                     users (home dir names) in the
                     comma-separated list
  --hosts      (-H)  only generate and send emails for the
                     output from the hosts in the
                     comma-separated list
  --todefault  (-t)  emails for which there is no entry in the
                     emailaddrs file get sent here (default:
                     no mail sent, a warning message displayed)
  --dryrun     (-D)  print messages, don't email them
"""
    sys.stderr.write(usage_message)
    sys.exit(1)


def get_date_formatted():
    '''
    return today's date in yymmdd format
    '''

    return time.strftime("%Y%m%d", time.gmtime())


def do_main():
    '''
    main entry point, do all the work
    '''
    audit_dir = 'audit_output_' + get_date_formatted()
    addr_list = 'homes_vs_addresses.txt'
    auditor_email = 'data_auditor@wikimedia.org'
    email_subject = 'Data retention audit'
    email_server = None
    form_mail_file = None
    users = None
    hosts = None
    to_default = None
    verbose = False
    dryrun = False

    try:
        (options, remainder) = getopt.gnu_getopt(
            sys.argv[1:], "a:d:f:m:s:F:u:H:t:vDh",
            ["auditdir=", "fromaddr=",
             "emailaddrs=", "mailserver=",
             "subject=", "formmail",
             "users=", "hosts=",
             "todefault=",
             "verbose", "dryrun", "help"])

    except getopt.GetoptError as err:
        usage("Unknown option specified: " + str(err))

    for (opt, val) in options:
        if opt in ["-a", "--emailaddrs"]:
            addr_list = val
        elif opt in ["-d", "--auditdir"]:
            audit_dir = val
        elif opt in ["-D", "--dryrun"]:
            dryrun = True
        elif opt in ["-f", "--fromaddr"]:
            auditor_email = val
        elif opt in ["-F", "--formmail"]:
            form_mail_file = val
        elif opt in ["-H", "--hosts"]:
            hosts = val
        elif opt in ["-m", "--mailserver"]:
            email_server = val
        elif opt in ["-s", "--subject"]:
            email_subject = val
        elif opt in ["-u", "--users"]:
            users = val
        elif opt in ["-t", "--todefault"]:
            to_default = val
        elif opt in ["-v", "--verbose"]:
            verbose = True
        elif opt in ["-h", "--help"]:
            usage("Help:\n")

    if len(remainder) > 0:
        usage("Unknown option(s) specified: <%s>"
              % remainder[0])

    if email_server is None:
        usage("No email server specified")

    if not os.path.exists(audit_dir):
        usage("No such directory: %s" % audit_dir)

    if not os.path.exists(addr_list):
        usage("No such email address file: %s" % addr_list)

    emailer = AuditEmailer(addr_list, audit_dir,
                           auditor_email, email_subject,
                           email_server, form_mail_file,
                           users, hosts, to_default,
                           verbose, dryrun)
    emailer.run()


if __name__ == '__main__':
    do_main()
