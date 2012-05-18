/* Simply dump database contents */
/* $Id: exporter.c 12318 2005-12-31 15:34:46Z midom $ */
#include <stdio.h>
#include "collector.h"

int main(int ac, char **av) {
dumpData(stdout);
return(0);
}
