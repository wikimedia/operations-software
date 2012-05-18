# Makefile for profile collector package
# $Id: Makefile 111618 2012-02-16 04:08:32Z tstarling $
#
#MacOSX Fink library paths 
#CFLAGS+=-I/sw/include/
#LDFLAGS+=-L/sw/lib/

LDLIBS+=-ldb
CFLAGS+=-Wall -g

all: collector exporter

collector: collector.c export.c

exporter: export.c exporter.c

#export: collector.h export.c

clean:
	rm -f collector exporter
