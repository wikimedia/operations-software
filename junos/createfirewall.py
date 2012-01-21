import os
import sys
import csv
import os.path
import datetime

# version 1.0;
# ns junos = "http://xml.juniper.net/junos/*/junos";
# ns xnm = "http://xml.juniper.net/xnm/1.1/xnm";
# ns jcs = "http://xml.juniper.net/junos/commit-scripts/1.0";
# import "../import/junos.xsl";

#file parameters defined here
outputfile = "test.slax"
sourcedir = "/Users/lcarr/firewall_python/test"
defaultheaders = "\n#This file should live in /var/db/scripts\n\
ns junos = \"http://xml.juniper.net/junos/*/junos\";\n\
ns xnm = \"http://xml.juniper.net/xnm/1.1/xnm\";\n\
ns jcs = \"http://xml.juniper.net/junos/commit-scripts/1.0\";\n\
import \"../import/junos.xsl\";\n"

def main():

#First write the generic information to the top of the file
    try:
        output = open(outputfile, 'w', 0)
        timestamp = datetime.datetime.now()
        output.write('# File automatically created at ' + str(timestamp))
        output.write(defaultheaders)
    except IOError:
        print (outputfile + ' output file has problems.')
        sys.exit(1)
#Then we start the actual code bits
    output.write('match configuration {\n\
    <change> {\n\
    \t<firewall>\n\
    \t\t<family>\n\
    \t\t\t<inet>\n\
    \t\t\t\t<filter> "autocreated4"\n')
#Now we need to take the various inputs in the directory and make them into slax terms

#Then grab
    try:
        files = os.listdir(sourcedir)
        for a in files:
            output.write('\t\t\t\t\t<term> "' + a + '"\n')
    except OSError:
        print('Something bad happened with the directory. Maybe it doesn\'t exist')

#Now we complete and close our configuration bit
    output.write('}\n')

#At the very very end, close the file
    output.close()
main()
sys.exit(0)