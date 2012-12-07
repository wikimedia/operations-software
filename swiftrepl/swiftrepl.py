#!/usr/bin/python

# Written by Mark Bergsma <mark@wikimedia.org>

import sys, re, collections, threading, time, traceback, httplib, socket, errno, random
import cloudfiles

from Queue import Queue

container_regexp = "^wikipedia-en-local-thumb.[0-9a-f]{2}$"

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

def replicate_object(srcobj, dstobj, srcconnpool, dstconnpool):
	dstobj.content_type = srcobj.content_type
	dstobj.etag = srcobj.etag
	dstobj.last_modified = srcobj.last_modified
	dstobj.size = srcobj.size
	dstobj.metadata = dict(srcobj.metadata)
	
	stream = srcobj.stream(chunksize=65536)

	# Replace the connections
	srcobj.container.conn = srcconnpool.get()
	dstobj.container.conn = dstconnpool.get()
	try:
		for i in range(2):
			try:
				dstobj.send(stream)
			except (AttributeError, httplib.CannotSendRequest, socket.error, httplib.ResponseNotReady):
				# httplib bug?
				continue
			except cloudfiles.errors.ResponseError as e:
				if e.status == 404:
					print "Object", srcobj.name.encode("ascii", errors="ignore"), "doesn't exist at the source after all. Skipping."
					break
				else:
					print "Error occurred, skipping"
					print e
					# FIXME
					break
			else:
				break
	finally:
		srcconnpool.put(srcobj.container.conn)
		dstconnpool.put(dstobj.container.conn)
		srcobj.container.conn, dstobj.container.conn = None, None

def get_container_objects(container, limit, marker, connpool):

	container.conn = connpool.get()
	try:
		objects = None
		while objects is None:
			try:
				objects = container.get_objects(limit=limit, marker=marker)
			except AttributeError:
				# httplib bug?
				continue
			except socket.timeout:
				continue
			except socket.error as e:
				if e.errno == errno.EAGAIN:
					continue
				else:
					print >> sys.stderr, e, traceback.format_exc()
					continue
			except httplib.ResponseNotReady:
				time.sleep(1000)
				continue
			except Exception as e:
				print >> sys.stderr, e, traceback.format_exc()
				continue
		else:
			return objects
	finally:
		connpool.put(container.conn)
		container.conn = None

def sync_container(srccontainer, srcconnpool, dstconnpool):
	global NOBJECT
	
	last = ''
	hits, processed, gets = 0, 0, 0

	dstconn = dstconnpool.get()
	try:
		try:
			dstcontainer = dstconn.get_container(srccontainer.name)
		except cloudfiles.errors.NoSuchContainer as e:
			dstcontainer = dstconn.create_container(srccontainer.name)
	finally:
		dstconnpool.put(dstconn)
		dstconn = None

	dstobjects = None
	while True:
		srcobjects = get_container_objects(srccontainer, limit=NOBJECT, marker=last, connpool=srcconnpool)

		limit = 10*NOBJECT
		while dstobjects is None or (len(dstobjects) >= limit and dstobjects[-1].name < srcobjects[-1].name):
			dstobjects = get_container_objects(dstcontainer, limit=limit, marker=last, connpool=dstconnpool)
			if len(dstobjects) == limit:
				limit *= 2
				if limit > 10000:
					dstobjects = None
					break

		for srcobj in srcobjects:
			processed += 1
			last = srcobj.name.encode("utf-8")
			objname = srcobj.name.encode("ascii", errors="ignore")
			msg = "%s\t%s\t%s\t%s\t%s" % (srccontainer.name, srcobj.etag, srcobj.size, objname, srcobj.last_modified)
			try:
				if dstobjects is not None:
					dstobj = dstobjects[dstobjects.index(srcobj.name)]
				else:
					gets += 1
					dstcontainer.conn = dstconnpool.get()
					try:
						dstobj = dstcontainer.get_object(srcobj.name)
					finally:
						dstconnpool.put(dstcontainer.conn)
						dstcontainer.conn = None
			except (ValueError, cloudfiles.errors.NoSuchObject) as e:
				print msg
				print "Destination does not have %s, syncing" % objname
				dstcontainer.conn = dstconnpool.get()
				try:
					dstobj = dstcontainer.create_object(srcobj.name)
				finally:
					dstconnpool.put(dstcontainer.conn)
					dstcontainer.conn = None
			else:
				if srcobj.etag != dstobj.etag:
					print msg
					print "%s\t%s\tE-Tag mismatch: %s/%s, syncing" % (srccontainer.name, objname, srcobj.etag, dstobj.etag)
				else:
					# Object already exists
					hits += 1
					continue
		
			replicate_object(srcobj, dstobj, srcconnpool, dstconnpool)

		print "STATS: %s processed: %d/%d (%d%%), hit rate: %d%%, gets: %d" % (srccontainer.name,
		                                                       processed, srccontainer.object_count,
		                                                       int(float(processed)/srccontainer.object_count*100),
		                                                       int(float(hits)/processed*100), gets)

		if len(srcobjects) < NOBJECT:
			break
		
	print "FINISHED:", srccontainer.name

def replicator_thread(*args, **kwargs):
	while True:
		try:
			container = containers.popleft()
			sync_container(container, kwargs['srcconnpool'], kwargs['dstconnpool'])
		except Exception as e:
			print >> sys.stderr, e, traceback.format_exc()
			print >> sys.stderr, "Abandoning container %s for now" % container
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
	containerlist = [container for container in srcconn.get_all_containers()
	                           if re.match(container_regexp, container.name)]
	random.shuffle(containerlist)
	containers = collections.deque(containerlist)
	srcconnpool.put(srcconn)

	# Start threads
	for i in range(int(sys.argv[1])):
		t = threading.Thread(target=replicator_thread, kwargs={'srcconnpool': srcconnpool, 'dstconnpool': dstconnpool})
		t.daemon = True
		t.start()
	
	while(True):
		time.sleep(1000)
