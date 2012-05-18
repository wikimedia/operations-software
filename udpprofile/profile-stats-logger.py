#!/usr/bin/python

import sys, time, os, os.path, math, pprint

sys.path.append( '/usr/lib/cgi-bin/ng' )
import config
from extractprofile import SocketProfile
import rrdtool

profId = 'stats/all'
rrdFileName = '/var/lib/profile-stats-logger/stats.rrd'

if not os.path.exists( rrdFileName ):
	rrdtool.create(
		rrdFileName,
		'--step', '10',
		'DS:pcache_hit:DERIVE:60:0:U',
		'DS:pcache_miss_absent:DERIVE:60:0:U',
		'DS:pcache_miss_expired:DERIVE:60:0:U',
		'DS:pcache_miss_invalid:DERIVE:60:0:U',
		'RRA:AVERAGE:0.1:1:8640', # 10s intervals for 24 hours
		'RRA:AVERAGE:0.1:30:8640', # 5 min intervals for 1 month
		'RRA:AVERAGE:0.1:360:8640' # 1 hour intervals for 1 year
		)

nextTime = math.floor(time.time() / 10) * 10 + 10

while True:
	t = time.time()
	while t < nextTime:
		time.sleep(nextTime - t)
		t = time.time()
	nextTime += 10

	try: 
		fullProfile = SocketProfile(config.host,config.port).extract()
	except:
		continue

	if not ( profId in fullProfile ):
		continue
	profile = fullProfile[profId]['-']
	if 'pcache_hit' not in profile:
		profile['pcache_hit'] = {'count':0}
	if 'pcache_miss_absent' not in profile:
		profile['pcache_miss_absent'] = {'count':0}
	if 'pcache_miss_expired' not in profile:
		profile['pcache_miss_expired'] = {'count':0}
	if 'pcache_miss_invalid' not in profile:
		profile['pcache_miss_invalid'] = {'count':0}


	rrdtool.update(
		rrdFileName,
		'N:' + str(profile['pcache_hit']['count']) +
		':' + str(profile['pcache_miss_absent']['count']) +
		':' + str(profile['pcache_miss_expired']['count']) +
		':' + str(profile['pcache_miss_invalid']['count'] ) )

