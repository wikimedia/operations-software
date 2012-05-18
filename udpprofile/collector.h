/* Collector structures and some headers and some data */
/* $Id: collector.h 102737 2011-11-11 01:52:57Z asher $ */

#include <stdio.h>
#include <db.h>
#define POINTS 300
DB *db;

/* Stats variables, not that generic, are they? */
struct pfstats {
	unsigned long pf_count;
	/* CPU time of event */
	double pf_cpu;
	double pf_cpu_sq;
	double pf_real;
	double pf_real_sq;
	int pf_real_pointer;
	double pf_reals[POINTS];
};

void dumpData(FILE *);

