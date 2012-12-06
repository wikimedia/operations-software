#!/usr/bin/python

# Written by Mark Bergsma <mark@wikimedia.org>

import sys, re, collections, threading, time, traceback, httplib, socket, errno
import cloudfiles

from Queue import Queue

container_regexp = "^wikipedia-en-local-public.[0-9a-f]{2}$"

NOBJECT=100

src = {}
dst = {}

class WorkingConnectionPool(cloudfiles.connection.ConnectionPool):
	def __init__(self, username=None, api_key=None, **kwargs):
		self.connargs = dict(kwargs)
		self.connargs.update({'username': username, 'api_key': api_key})
		self.timeout = kwargs.get('timeout', 5)
		poolsize = kwargs.get('poolsize', 10)
		Queue.__init__(self, poolsize)

def connect(params):
	return WorkingConnectionPool(
		username=(params['username'] or None),
		api_key=(params['api_key'] or None),
		authurl=params['auth_url'],
		timeout=60)

def replicate_object(srcobj, dstobj):
	dstobj.content_type = srcobj.content_type
	dstobj.etag = srcobj.etag
	dstobj.last_modified = srcobj.last_modified
	dstobj.size = srcobj.size
	dstobj.metadata = dict(srcobj.metadata)
	
	stream = srcobj.stream(chunksize=65536)
	
	for i in range(2):
		try:
			dstobj.send(stream)
		except (AttributeError, httplib.CannotSendRequest):
			# httplib bug?
			continue
		except cloudfiles.errors.ResponseError, e:
			if e.status == 404:
				print "Object", srcobj.name, "doesn't exist at the source after all. Skipping."
				break
			else:
				print "Error occurred, skipping"
				print e
				# FIXME
				break
		else:
			break

def sync_container(srccontainer, srcconnpool, dstconnpool):
	global NOBJECT
	
	srcconn = srcconnpool.get()
	dstconn = dstconnpool.get()
	last = ''
	hits, processed = 0, 0

	try:
		dstcontainer = dstconn.get_container(srccontainer.name)
	except cloudfiles.errors.NoSuchContainer, e:
		dstcontainer = dstconn.create_container(srccontainer.name)

	while True:
		try:
			srcobjects = srccontainer.get_objects(limit=NOBJECT, marker=last)
		except AttributeError:
			# httplib bug?
			continue
		except socket.error, e:
			if e.errno == errno.EAGAIN: continue
		dstobjects = None

		limit = 10*NOBJECT
		while dstobjects is None or (len(dstobjects) == limit and dstobjects[-1].name < srcobjects[-1].name):
			try:
				dstobjects = dstcontainer.get_objects(limit=limit, marker=last)
			except AttributeError:
				# httplib bug?
				continue
			except socket.error, e:
				if e.errno == errno.EAGAIN: continue

			if len(dstobjects) == limit:
				limit *= 2
				if limit > 10000:
					dstobjects = None
					break

		for srcobj in srcobjects:
			processed += 1
			last = srcobj.name
			msg = "%s\t%s\t%s\t%s\t%s" % (srccontainer.name, srcobj.etag, srcobj.size, srcobj.name, srcobj.last_modified)
			try:
				if dstobjects is not None:
					dstobj = dstobjects[dstobjects.index(srcobj.name)]
				else:
					dstobj = dstcontainer.get_object(srcobj.name)
			except (ValueError, cloudfiles.errors.NoSuchObject), e:
				print msg
				print "Destination does not have %s, syncing" % srcobj.name
				dstobj = dstcontainer.create_object(srcobj.name)
			else:
				if srcobj.etag != dstobj.etag:
					print msg
					print "%s\t%s\tE-Tag mismatch: %s/%s, syncing" % (srccontainer.name, dstobj.name, srcobj.etag, dstobj.etag)
				else:
					# Object already exists
					hits += 1
					continue
		
			replicate_object(srcobj, dstobj)

		print "STATS: %s processed: %d/%d (%d%%), hit rate: %d%%" % (srccontainer.name,
		                                                       processed, srccontainer.object_count,
		                                                       int(float(processed)/srccontainer.object_count*100),
		                                                       int(float(hits)/processed*100))

		if len(srcobjects) < NOBJECT:
			break
		
	print "FINISHED:", srccontainer.name

def replicator_thread(*args, **kwargs):
	while True:
		try:
			container = containers.popleft()
			sync_container(container, kwargs['srcconnpool'], kwargs['dstconnpool'])
		except Exception, e:
			print e, traceback.format_exc()
			time.sleep(10);
		finally:
			containers.append(container)


def parse_cli_params():
	global src, dst

	# FIXME
	src['username'], src['api_key'], src['auth_url'], dst['username'], dst['api_key'], dst['auth_url'] = [l.strip() for l in file('swiftrepl.conf')]

if __name__ == '__main__':
	parse_cli_params()
	
	srcconnpool = connect(src)
	dstconnpool = connect(dst)
	
	srcconn = srcconnpool.get()
	containers = collections.deque([container
	                                  for container in srcconn.get_all_containers()
	                                  if re.match(container_regexp, container.name)])
	srcconnpool.put(srcconn)

	# Start threads
	for i in range(int(sys.argv[1])):
		t = threading.Thread(target=replicator_thread, kwargs={'srcconnpool': srcconnpool, 'dstconnpool': dstconnpool})
		t.daemon = True
		t.start()
	
	while(True):
		time.sleep(1000)
