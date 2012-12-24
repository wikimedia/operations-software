#!/usr/bin/python

# Written by Mark Bergsma <mark@wikimedia.org>

import sys, re, collections, threading, time, traceback, httplib, socket, errno, random
import cloudfiles, cloudfiles.errors

from Queue import Queue

container_regexp = sys.argv[2] #"^wikipedia-en-local-thumb.[0-9a-f]{2}$"
copy_headers = re.compile(r'^X-Content-Duration$', flags=re.IGNORECASE)

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

def object_stream_prepare(obj, hdrs=None):
	obj._name_check()
	response = obj.container.conn.make_request('GET',
	    path=[obj.container.name, obj.name], hdrs=hdrs)
	if response.status < 200 or response.status > 299:
		buff = response.read()
		raise cloudfiles.errors.ResponseError(response.status, response.reason)
	return response

def object_stream(response, chunksize=8192):
	buff = response.read(chunksize)
	while len(buff) > 0:
		yield buff
		buff = response.read(chunksize)
	# I hate you httplib
	buff = response.read()

def copy_metadata(response, dstobj, headers={}):
	global copy_headers

	for hdr in response.getheaders():
		if copy_headers.match(hdr[0]):
			hdrname = "-".join([seg.capitalize() for seg in hdr[0].split("-")])
			headers[hdrname] = hdr[1]
			print "Copying custom header", hdrname, hdr[1]
		elif hdr[0].lower().startswith('x-object-meta-'):
			dstobj.metadata[hdr[0][14:]] = hdr[1]

def send_object(dstobj, iterable, headers={}):
	"""
	Imported and modified from cloudfiles.storage_object.Object.send,
	to allow specifying custom headers
	"""
	assert dstobj.size is not None
	
	from cloudfiles.utils import unicode_quote

	if not dstobj.content_type:
		dstobj.content_type = 'application/octet-stream'

	path = "/%s/%s/%s" % (dstobj.container.conn.uri.rstrip('/'), \
			unicode_quote(dstobj.container.name), unicode_quote(dstobj.name))
	headers.update(dstobj._make_headers())
	
	headers['X-Auth-Token'] = dstobj.container.conn.token
	headers['User-Agent'] = dstobj.container.conn.user_agent
	http = dstobj.container.conn.connection
	http.putrequest('PUT', path)
	for key, value in headers.iteritems():
		http.putheader(key, value)
	http.endheaders()

	response = None
	transferred = 0
	try:
		for chunk in iterable:
			http.send(chunk)
			transferred += len(chunk)
		# If the generator didn't yield enough data, stop, drop, and roll.
		if transferred < dstobj.size:
			raise cloudfiles.errors.IncompleteSend()
		response = http.getresponse()
		buff = response.read()
	except cloudfiles.errors.timeout, err:
		if response:
			# pylint: disable-msg=E1101
			response.read()
		raise err

	if (response.status < 200) or (response.status > 299):
		raise cloudfiles.errors.ResponseError(response.status, response.reason)

	for hdr in response.getheaders():
		if hdr[0].lower() == 'etag':
			dstobj._etag = hdr[1]

def replicate_object(srcobj, dstobj, srcconnpool, dstconnpool):
	# Replace the connections
	srcobj.container.conn = srcconnpool.get()
	dstobj.container.conn = dstconnpool.get()
	
	try:
		for i in range(3):
			try:
				# Start source GET request
				response = object_stream_prepare(srcobj)

				dstobj.content_type = srcobj.content_type
				dstobj.etag = srcobj.etag
				dstobj.last_modified = srcobj.last_modified
				dstobj.size = srcobj.size
				dstobj.metadata = dict(srcobj.metadata)
				headers = {}
				copy_metadata(response, dstobj, headers)
				send_object(dstobj, object_stream(response, chunksize=65536), headers)
			except httplib.CannotSendRequest as e:
				srcobj.container.conn = srcconnpool.get()
				dstobj.container.conn = dstconnpool.get()
				continue
			except (AttributeError, socket.error, httplib.ResponseNotReady, httplib.BadStatusLine) as e:
				# httplib bug?
				time.sleep(1)
				continue
			except cloudfiles.errors.ResponseError as e:
				if e.status == 404:
					# File was deleted
					pass
				else:
					print "Error occurred, skipping"
					print e
					# FIXME
				break
			except Exception as e:
				continue
			else:
				break
		else:
			print >> sys.stderr, "Repeated error in replicate_object"
			raise e
		srcconnpool.put(srcobj.container.conn)
		dstconnpool.put(dstobj.container.conn)		
	finally:
		srcobj.container.conn, dstobj.container.conn = None, None

def get_container_objects(container, limit, marker, connpool):

	container.conn = connpool.get()
	try:
		objects = None
		for i in range(3):
			try:
				objects = container.get_objects(limit=limit, marker=marker)
			except AttributeError as e:
				# httplib bug?
				continue
			except socket.timeout as e:
				continue
			except socket.error as e:
				if e.errno == errno.EAGAIN:
					continue
				else:
					print >> sys.stderr, e, traceback.format_exc()
					continue
			except httplib.ResponseNotReady as e:
				time.sleep(1)
				continue
			except Exception as e:
				print >> sys.stderr, e, traceback.format_exc()
				continue
			else:
				return objects
		else:
			print >> sys.stderr, "Repeated error in get_container_objects"
			raise e
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
				#print msg
				#print "Destination does not have %s, syncing" % objname
				object_record = dict.fromkeys(['content_type', 'bytes', 'last_modified', 'hash'], None)
				object_record['name'] = srcobj.name
				dstobj = cloudfiles.storage_object.Object(dstcontainer, object_record=object_record)
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
	
	while True:
		time.sleep(10)
