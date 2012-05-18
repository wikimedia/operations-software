#!/usr/bin/python
import sys, os, rrdtool, cgi, cgitb

cgitb.enable()

form = cgi.SvFormContentDict()
if 'period' in form:
	if form['period'].endswith( 'h' ):
		period = int( form['period'][0:-1] ) * 60
	elif form['period'].endswith( 'd' ):
		period = int( form['period'][0:-1] ) * 60 * 24
	else:
		period = int( form['period'] )
else:
	period = 30

print 'Content-Type: image/png'
print 'Cache-Control: no-cache'
print

rrdFileName = '/var/lib/profile-stats-logger/stats.rrd'
graph = [
	'-',
	'--start', '-' + str( period ) + 'm',
	'--width', '800',
	'--height', '500',
	'--vertical-label', 'Request rate (req/s)',
	'--title', 'Parser cache request rate (all wikis)',
	'--lower-limit', '0',
	'DEF:pcache_hit=' + rrdFileName + ':pcache_hit:AVERAGE',
	'DEF:pcache_miss_absent=' + rrdFileName + ':pcache_miss_absent:AVERAGE',
	'DEF:pcache_miss_expired=' + rrdFileName + ':pcache_miss_expired:AVERAGE',
	'DEF:pcache_miss_invalid=' + rrdFileName + ':pcache_miss_invalid:AVERAGE',
	'CDEF:total=pcache_hit,pcache_miss_absent,pcache_miss_expired,pcache_miss_invalid,+,+,+',
	'CDEF:total_avg_300=total,300,TREND',
	'LINE:total#000080',
]
if period < 1440:
	graph.append('LINE:total_avg_300#ff0000')

rrdtool.graph(*graph)

