#!/usr/bin/python


## for this import to work, move swiftcleaner to swiftcleaner.py
#import swiftcleaner
#
#fh=open('testimages.list')
#objlist = []
#for line in fh.readlines():
#    (cont, image) = line[:-1].split()
#    objlist.append((cont, image))
#
#c = swiftcleaner.CheckObjects(objlist)
#c.run()

#import re
#fh = open("purgebadimages/lists/wikipedia-commons-local-thumb.a2.list")
#for line in fh.readlines():
#  m = re.match("(temp/|archive/)?./../(\d+!)?(?P<media>[^/]+)/(?P<prefix>.*)-(?P=media)(.jpg|.png)?(?P<cruft>.*)$", line)
#  if m:
#    if(m.group('cruft')):
#      print "bQd image: %s %s %s %s" % (m.group('media'), m.group('prefix'), m.group('cruft'), line),
#  else:
#    print "bad image: %s" % line,
#  #print "checked i: %s" % line

# vim: set nu list expandtab tabstop=4 shiftwidth=4 autoindent:
