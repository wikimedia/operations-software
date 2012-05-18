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
	'--upper-limit', '100',
	'--lower-limit', '0',
	'--rigid',
	'--title', 'Parser cache ratios (all wikis)',
	'--vertical-label', 'Ratio (%)',
	'DEF:pcache_hit=' + rrdFileName + ':pcache_hit:AVERAGE',
	'DEF:pcache_miss_absent=' + rrdFileName + ':pcache_miss_absent:AVERAGE',
	'DEF:pcache_miss_expired=' + rrdFileName + ':pcache_miss_expired:AVERAGE',
	'DEF:pcache_miss_invalid=' + rrdFileName + ':pcache_miss_invalid:AVERAGE',
	'CDEF:total=pcache_hit,pcache_miss_absent,pcache_miss_expired,pcache_miss_invalid,+,+,+',
	'CDEF:pcache_hit_percent=100,pcache_hit,total,/,*',
	'CDEF:pcache_miss_absent_percent=100,pcache_miss_absent,total,/,*',
	'CDEF:pcache_miss_expired_percent=100,pcache_miss_expired,total,/,*',
	'CDEF:pcache_miss_invalid_percent=100,pcache_miss_invalid,total,/,*',
	'CDEF:pcache_hit_avg=pcache_hit_percent,120,TREND',
	'AREA:pcache_hit_percent#00ff00:Hit %:STACK',
	'AREA:pcache_miss_absent_percent#ffff00:Miss (absent) %:STACK',
	'AREA:pcache_miss_expired_percent#ff8888:Miss (expired) %:STACK',
	'AREA:pcache_miss_invalid_percent#ff0000:Miss (invalid) %:STACK',
]
if period < 1440:
	graph.append('LINE:pcache_hit_avg#000080:Hit % (2 min. avg)')

rrdtool.graph(*graph)
