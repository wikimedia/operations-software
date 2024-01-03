#!/bin/bash

# Check if all arguments are provided
if [ "$#" -ne 7 ]; then
    echo "Usage: ./script.sh <host> <instance> <section> <DC> <rack> <port>"
    echo "  - host: FQDN (Fully Qualified Domain Name)"
    echo "  - instance: Name of the instance"
    echo "  - section: Section name"
    echo "  - DC: Datacenter"
    echo "  - rack: Rack information"
    echo "  - port: Mariadb port number"
    exit 1
fi

HOST="$1"
INSTANCE="$2"
SECTION="$3"
DC="$4"
RACK="$5"
PORT="$6"

# Extracting the hostname from FQDN
hostname=$(echo "$HOST" | cut -d'.' -f1)

# Creating SQL queries
insert_instances="INSERT INTO instances (name, server, port, \`group\`) VALUES ('$INSTANCE','$HOST',$PORT, 'dbstore');"
insert_section_instances="INSERT INTO section_instances (instance, section) VALUES ('$INSTANCE:$PORT','$SECTION');"
insert_servers="INSERT INTO servers (fqdn, hostname, dc, rack) VALUES ('$HOST','$hostname', '$DC', '$RACK');"

# Warning about script behavior
echo "WARNING: This script only prints SQL queries. It does not execute them."
echo

# Printing SQL queries
echo "$insert_instances"
echo "$insert_section_instances"
echo "$insert_servers"

