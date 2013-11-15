#!/usr/bin/python

##
##  multithreaded python script to call all the URLs in a list
##  with configurable delay between calls and number of threads
##  must be passed in the name of a file containing a list of URLs
##
##
##  the purpose of this script is to consume a listing of all the
##  thumbnails on ms5 and call out to swift, populating it via
##  the 404 handler running there.
##
##  Author: Ben Hartshorne
##  Copyright (c) 2011 Wikimedia Foundation
##  License: Released under the GPL v2 or later.
##  For a full description of the license, please visit http://www.gnu.org/licenses/gpl-2.0.html
##

from urllib import urlopen
from optparse import OptionParser
import time
import datetime

import threading
import os

class UrlCaller(threading.Thread):
    '''a threaded object that will call URLs from the urllist'''

    # the filehandle of the open url list file
    urlfh = None
    # a global urllist shared between all threads
    urllist=[]
    # the index of the next url to be read - lock this with self.poslock b/f editing
    position=0
    # the number of URLs we've tried so far
    tried=0
    # the number of URLs that have failed so far - lock this with failedlock b/f editing
    failed=0
    # the time we started working
    starttime = None
    num_lines = 0
    total_lines = 0
    # timing storage
    queryduration_exception = []
    queryduration_success = []
    queryduration_failed = []

    # passed in - cmd line options though all we really need is delay
    def __init__(self, options):
        threading.Thread.__init__(self)
        self.delay = options.delay
        self.num_lines = UrlCaller.num_lines
        self.poslock = threading.Lock()
        self.failedlock = threading.Lock()
        self.tryinglock = threading.Lock()

        self.print_status_num = int(min(UrlCaller.total_lines / 10, 100000))

    # thread entry.
    # go through urllist, exit when done
    def run(self):
        url = self.get_url()
        while url:
            # skip comments and empty lines
            url = url.strip()
            if(len(url) <= 1 or url.startswith('#')):
                url = self.get_url()
                continue
            self.call_url(url)
            url = self.get_url()
            if self.delay:
                time.sleep(self.delay)

    # set the urllist globally
    @classmethod
    def set_urllist(cls, urls):
        UrlCaller.urllist = urls
        UrlCaller.num_lines = len(urls)

    # set the urllist filehandle globally
    # takes an open filehandle and a chunksize (0 = infinite)
    # FIXME set_urllist needs to be called with a chunk before calling this but it shouldn't
    @classmethod
    def set_urlfh(cls, fh, chunk, position):
        UrlCaller.urlfh = fh
        UrlCaller.chunk = chunk
        filesize = os.fstat(fh.fileno()).st_size  # size in bytes
        if position:
            # if we were suposed to start part way through the file, only count the remaining % of the file
            filesize = int((float(filesize) * position / 100))
        if (filesize > chunk and chunk != 0):
            UrlCaller.total_lines = len(UrlCaller.urllist) * (float(filesize) / chunk)
        else:
            UrlCaller.total_lines = len(UrlCaller.urllist)

    # set position in the urllist
    # used when you don't want to start at the beginning
    @classmethod
    def set_position(cls, pos):
        UrlCaller.position = pos

    # set the starttime globally
    @classmethod
    def set_starttime(cls, start):
        UrlCaller.starttime = start

    # get the next URL to load
    # returns a url or None if we're finished
    # prints status every so often
    def get_url(self):
        self.poslock.acquire()
        pos = UrlCaller.position
        try:
            url = UrlCaller.urllist[pos]
            UrlCaller.position += 1
        except IndexError:
            # we're done with our chunk - read in some more!
            UrlCaller.urllist = UrlCaller.urlfh.readlines(UrlCaller.chunk)
            if (len(UrlCaller.urllist) == 0):
                # if we're really done
                url = None
            else:
                # return the first URL and keep going
                url = UrlCaller.urllist[0]
                UrlCaller.position = 1
        self.poslock.release()

        #only print status every print_status_num requests, and skip 100%
        tried = UrlCaller.tried
        if(tried > 0 and url and not tried % self.print_status_num):
            # lock both counters so we get a consistent view
            # note that pos here is likely different from pos right above
            # so it may not be an even number
            self.poslock.acquire()
            self.failedlock.acquire()
            self.tryinglock.acquire()
            self.print_status()
            self.tryinglock.release()
            self.failedlock.release()
            self.poslock.release()
            percent_done = 100 * tried / self.total_lines
            curtime = datetime.datetime.now()
            exectime = curtime - self.starttime
            #print("status report: progress: %s%%, %s URLs tried, %s URLs failed, execution time: %s" %\
            #        (int(percent_done) + 1, tried, fail, exectime))
        return url

    @classmethod
    def print_status(cls):
        pos = UrlCaller.position
        tried = UrlCaller.tried
        fail = UrlCaller.failed
        percent_done = 100 * tried / UrlCaller.total_lines
        curtime = datetime.datetime.now()
        exectime = curtime - UrlCaller.starttime
        print("status report: progress: %s%%, %s URLs tried, %s URLs failed, execution time: %s" %
              (int(percent_done) + 1, tried, fail, exectime))

    @classmethod
    def crunch_querydur_stats(cls):
        '''calculate statistics around query duration'''
        exceptions = cls.queryduration_exception[:]
        failed = cls.queryduration_failed[:]
        success = cls.queryduration_success[:]
        exceptions.sort()
        exceptions.reverse()
        failed.sort()
        failed.reverse()
        success.sort()
        success.reverse()
        min_dur = 0
        max_dur = 0
        for l in [exceptions, failed, success]:
            try:
                min_dur = min(l)
                max_dur = max(l)
            except ValueError:
                pass
        #min_dur = min(min(exceptions),min(failed),min(success))
        #max_dur = max(max(exceptions),max(failed),max(success))

        # count durations - bucket them by dur length
        dur_buckets = {}
        num_durs = {}
        for l in ['exceptions', 'failed', 'success']:
            queries = locals()[l]
            dur_buckets[l] = {}
            cur_dur = 0
            min_dur_range = 0
            max_dur_range = 0
            # iterate from 0 to the longest duration query
            while len(queries) > 0 and cur_dur <= max(queries):
                min_dur_range = cur_dur
                max_dur_range = int(cur_dur * 1.25)
                key = "%s-%s" % (min_dur_range, max_dur_range)
                dur_buckets[l][key] = 0
                # iterate from the current index to 150% of that duration
                while cur_dur <= max_dur_range:
                    # if queries is empty, we're done
                    if len(queries) == 0:
                        cur_dur += 1
                        continue
                    # if the currently lowest duration is lower than our max range, add it to the bucket
                    if queries[-1] <= max_dur_range:
                        queries.pop()
                        dur_buckets[l][key] += 1
                    else:
                        # we've collected all the durations that belong in this bucket
                        # bump the counter to the next bucket
                        cur_dur = max_dur_range + 1

            num_durs[l] = sum(int(x) for x in dur_buckets[l].values())
            # if a list is empty, set the num to 1 to protect against div-by-zero later
            num_durs[l] = (1 if num_durs[l] == 0 else num_durs[l])
        # clear out empty hash buckets
        for key in dur_buckets['success'].keys():
            # make sure the buckets exist in the other lists
            for l in ['failed', 'exceptions']:
                try:
                    dur_buckets[l][key] += 0
                except KeyError:
                    dur_buckets[l][key] = 0
            if dur_buckets['success'][key] == 0 \
                    and dur_buckets['failed'][key] == 0 \
                    and dur_buckets['exceptions'][key] == 0:
                del dur_buckets['success'][key]
                del dur_buckets['failed'][key]
                del dur_buckets['exceptions'][key]

        # sort based on the first number in the ###-### key
        dur_buckets_keys = dur_buckets['success'].keys()
        dur_buckets_keys.sort(lambda x,y: cmp(int(x), int(y)), lambda x: x.split('-')[0])
        print "Query duration report:"
        print "       dur: number of queries that took within <dur> range (in milliseconds)"
        print "               successes         failures        exceptions"
        for key in dur_buckets_keys:
            sucval = dur_buckets['success'][key]
            try:
                failval = dur_buckets['failed'][key]
            except KeyError:
                failval = 0
            try:
                excval = dur_buckets['exceptions'][key]
            except KeyError:
                excval = 0
            print(" %9s: %5s  (%2s%%)  |  %5s  (%2s%%)  |  %5s  (%2s%%)" %
                  (key, sucval, int(float(sucval) / num_durs['success'] * 100),
                   failval, int(float(failval) / num_durs['failed'] * 100),
                   excval, int(float(excval) / num_durs['exceptions'] * 100)))

    # call out to the net and retrieve the URL
    # record failures, throw away success
    def call_url(self, url=None):
        self.tryinglock.acquire()
        UrlCaller.tried += 1
        self.tryinglock.release()
        try:
            starttime = datetime.datetime.now()
            req = urlopen(url)
        except IOError as e:
            # urlopen throws an exception on HTTP 401 but not on 404.
            endtime = datetime.datetime.now()
            dur = endtime - starttime
            # store timing data in milliseconds
            self.queryduration_exception.append(int((dur.seconds * 1000000) + dur.microseconds / 1000))
            print("  error %s: %s" % (e[1], url))
            self.failedlock.acquire()
            UrlCaller.failed += 1
            self.failedlock.release()
            return
        endtime = datetime.datetime.now()
        dur = endtime - starttime
        # store the HTTP return code from the query
        resp = req.getcode()
        if resp != 200:
            self.queryduration_failed.append(int((dur.seconds * 1000000) + dur.microseconds / 1000))
            print("  error %s: %s" % (resp, url))
            self.failedlock.acquire()
            UrlCaller.failed += 1
            self.failedlock.release()
        else:
            self.queryduration_success.append(int((dur.seconds * 1000000) + dur.microseconds / 1000))

class PrintStatus(threading.Thread):
    '''a class that prints current status when the user hits return'''
    timer_thread = None
    def __init__(self, timer_thread):
        threading.Thread.__init__(self)
        self.timer_thread = timer_thread

    def run(self):
        while(True):
            raw_input()
            UrlCaller.print_status()
            UrlCaller.crunch_querydur_stats()
            self.timer_thread.print_full_stats()

class TimingCollector(threading.Thread):
    '''a class to collect per-second throughput data.
       maintains how many qps have gone by the previous second, the previous 5
       seconds and 30 seconds, and a hash of how many seconds have a specific
       qps throughput (i.e. there were 26 seconds during which throughput was
       110qps)'''
    cur_sec = 0
    last_five_sec = [0,0,0,0,0]
    last_thirty_sec = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
    throughput_frequency = {}
    last_pos = 0
    def __init__(self):
        threading.Thread.__init__(self)
        cur_sec = 0
        last_five_sec = [0,0,0,0,0]
        last_thirty_sec = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
        throughput_frequency = {}
        last_pos = 0

    def run(self):
        #self.setDaemon(True)
        while True:
            # populate cur_sec, last_*_sec
            self.collect_positions()
            # wait a second, then do it all over again.
            time.sleep(1)

    def collect_positions(self):
        cur_time = datetime.datetime.now().second
        cur_pos = UrlCaller.tried
        # cur_sec hold how many queries we hit this most recent second
        self.cur_sec = cur_pos - self.last_pos
        self.last_five_sec[cur_time % 5] = self.cur_sec
        self.last_thirty_sec[cur_time % 30] = self.cur_sec
        # add cur_sec to overall stats
        try:
            self.throughput_frequency[self.cur_sec] += 1
        except KeyError:
            self.throughput_frequency[self.cur_sec] = 1
        # get ready for the next run
        self.last_pos = cur_pos

    def get_curent_throughput(self):
        pass
    def get_5s_avg_throughput(self):
        pass
    def get_30s_avg_throughput(self):
        pass
    def get_oveall_stats(self):
        pass
    def print_short_stats(self):
        '''prints a one-liner with curren, 5s, and 30s throughput'''
        five_avg = sum(int(x) for x in self.last_five_sec) / 5
        thirty_avg = sum(int(x) for x in self.last_thirty_sec) / 30
        print ("Current throughput: %s queries per second.  Last 5s avg: %sqps.  Last 30s avg: %sqps" %
               (self.cur_sec, five_avg, thirty_avg))
    def print_full_stats(self):
        '''Prints a few bucketted counts for throughput stats.'''
        tp_hash = self.throughput_frequency
        tp_keys = tp_hash.keys()
        tp_keys.sort()
        new_perf = {}
        new_perf_keys = []
        # if fewer than 10 items, just print.
        #if len(tp_keys) < 10:
        #    new_perf = self.throughput_frequency
        # now for some fancy footwork.  To decrease the number of lines printed, combine nearby stats.
        # for each key, calculate 10%.  Sum all keys that show up between key and key+10%, then report as key + 5% +-5%
        tp_keys.reverse()  # work from small numbers up
        real_max = tp_keys[0]
        while len(tp_keys) > 0:
            key = tp_keys.pop()
            if(key == 0):
                next
            perfsum = 0
            min_key = key
            max_key = key + int(float(key) * 0.1)
            while key < max_key:
                # add the key's value to the sum if it exists
                perfsum += tp_hash[key]
                # remove it from the list
                try:
                    key = tp_keys.pop()
                except IndexError:
                    # tp_keys is empty
                    key = max_key
                    tp_keys = None
            # use the range of values covered as the key
            new_perf["%s-%s" % (min_key, max_key)] = perfsum
            # push the last one back onto the stack for the next round
            try:
                tp_keys.append(key)
            except AttributeError:
                # tp_keys was unset above
                # reset to an empty list so the next while loop will fail
                tp_keys = []
        new_perf_keys = new_perf.keys()
        # sort based on the first number in the ###-### key
        new_perf_keys.sort(lambda x,y: cmp(int(x), int(y)), lambda x: x.split('-')[0])
        num_seconds = sum(int(x) for x in new_perf.values())

        print "Throughput report:"
        print "       qps: number of seconds during which performance was in that qps range"
        for key in new_perf_keys:
            print(" %9s: %5s   (%2s%%)" % (key, new_perf[key], int(float(new_perf[key]) / num_seconds * 100)))


def main():
    # set up command line arguments
    usage="""usage: %prog [options] urllist

    Calls all the URLs in urllist, throwing away the data.  """
    parser = OptionParser(usage)
    parser.add_option("-d", dest="delay", default=0, help="delay in milliseconds between calling URLs. default %default")
    parser.add_option("-t", dest="num_threads", default=1, help="number of threads.  default %default")
    parser.add_option("-r", dest="resume", default=0, help="start <resume>% of the way through the urllist. range 1-100")
    parser.add_option("-c", dest="chunk", default=100, help="Number of MB to read from urllist at a time.  0 is all.  default %default")
    (options, args) = parser.parse_args()

    #convert millisec to seconds for sleep()
    options.delay = float(options.delay) / 1000
    # convert num_threads, chunk, and position to int so we can do MATHS
    num_threads = int(options.num_threads)
    chunk = int(float(options.chunk) * 1048576)  # convert from bytes to MB
    position = float(options.resume)

    # make sure we've got a urllist passed in
    if not args:
        print "Error: urllist required"
        parser.print_help()
        exit(1)

    # record our starting time so we can show stats at the end
    starttime = datetime.datetime.now()

    # open the file, seek to the middle if necessary, then set up the UrlCaller class
    urlfh = open(args[0])
    # if -r was specified, start % way through the list
    if position:
        filesize = os.fstat(urlfh.fileno()).st_size
        urlfh.seek(int(float(filesize) * position / 100))
        # throw out one line because we're probably in the middle of it
        urlfh.readline()
    # set up the UrlCaller class
    urls = urlfh.readlines(chunk)
    UrlCaller.set_urllist(urls)
    UrlCaller.set_urlfh(urlfh, chunk, position)
    UrlCaller.set_starttime(starttime)

    # print header
    print ""
    print "   About to start calling all these URLs."
    print "   I'll print status every 10% or 100k lines"
    print "   Press <return> at any time for current status."
    print ""
    print("Ok, starting %s%% of the way through the file." % int(position))

    # launch threads to go through the urllist
    threads = {}
    for i in range(num_threads):
        uc = UrlCaller(options)
        uc.start()
        threads[i] = uc

    # start up the status printing and timing thread
    timer = TimingCollector()
    timer.setDaemon(True)
    timer.start()
    status_printer = PrintStatus(timer)
    status_printer.setDaemon(True)
    status_printer.start()

    # wait until we're done before joining the threads
    # so that we can catch ctrl-c
    try:
        while len(UrlCaller.urllist) != 0:
            time.sleep(0.5)  # 1/2 second is reasonably responsive
    except KeyboardInterrupt:
        #set postition to the end so that all the threads think they're done
        urlfh.seek(0, os.SEEK_END)
        UrlCaller.position = len(urls)

    # pick up all the threads
    for num in threads.iterkeys():
        threads[num].join()

    # calculate final stats and print summary
    endtime = datetime.datetime.now()
    exectime = endtime - starttime
    print("Final summary: total: %s, failed: %s, execution time: %s" % (UrlCaller.tried, UrlCaller.failed, exectime))
    UrlCaller.crunch_querydur_stats()
    timer.print_full_stats()

if __name__ == '__main__':
    main()
