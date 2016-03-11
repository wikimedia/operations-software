#!/bin/bash

# fixme set SSH here to what you use
SSH=""

if [ -z "$SSH" ]; then
    echo "edit this script to put your ssh command"
    exit 1
fi

if [ -z "$1" ]; then
    echo "Usage: $0 filename [realm]"
    echo "filename should have list of fqdn of instances to check, one per line"
    echo "realm is optional and should be one of 'ops', 'prod', 'opslabs' or 'labs'. default is opslabs"
    exit 1
fi

case "$2" in
 'ops')
    BASTION="iron.wikimedia.org" ;;
 'prod')
    BASTION="bast1001.wikimedia.org" ;;
 'opslabs')
    BASTION="bastion-restricted.wmflabs.org" ;;
 'labs')
    BASTION="bastion.wmflabs.org" ;;
 *)
    BASTION="bastion-restricted.wmflabs.org" ;;
esac

hostlist=`cat $1`

for minion in $hostlist; do
    echo "doing $minion - using bastion $BASTION"
        $SSH $BASTION ssh -l root -o 'StrictHostKeyChecking=no' "$minion" "ls -lt /var/log/salt/minion"
        $SSH $BASTION ssh -l root -o 'StrictHostKeyChecking=no' "$minion" "tail -20 /var/log/salt/minion"
        $SSH $BASTION ssh -l root -o 'StrictHostKeyChecking=no' "$minion" "cat /etc/salt/minion"
        $SSH $BASTION ssh -l root -o 'StrictHostKeyChecking=no' "$minion" "ps axuww | grep salt | grep -v axuww"
        $SSH $BASTION ssh -l root -o 'StrictHostKeyChecking=no' "$minion" "dpkg -l | grep salt"
        $SSH $BASTION ssh -l root -o 'StrictHostKeyChecking=no' "$minion" "cat /etc/issue"
        $SSH $BASTION ssh -l root -o 'StrictHostKeyChecking=no' "$minion" "ls -lt /var/log/puppet.log"
        $SSH $BASTION ssh -l root -o 'StrictHostKeyChecking=no' "$minion" "tail -40 /var/log/puppet.log"
done
