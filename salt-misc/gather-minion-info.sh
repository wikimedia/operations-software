#!/bin/bash

# fixme set SSH here to what you use
SSH=""

if [ -z "$SSH" ]; then
    echo "edit this script to put your ssh command"
    exit 1
fi

if [ -z "$1" ]; then
    echo "Usage: $0 filename"
    echo "filename should have list of fqdn of instances to check, one per line"
    exit 1
fi
hostlist=`cat $1`

for minion in $hostlist; do
    echo "doing $minion"
        $SSH bastion-restricted.wmflabs.org ssh -l root -o 'StrictHostKeyChecking=no' "$minion" "ls -lt /var/log/salt/minion"
        $SSH bastion-restricted.wmflabs.org ssh -l root -o 'StrictHostKeyChecking=no' "$minion" "tail -20 /var/log/salt/minion"
        $SSH bastion-restricted.wmflabs.org ssh -l root -o 'StrictHostKeyChecking=no' "$minion" "cat /etc/salt/minion"
        $SSH bastion-restricted.wmflabs.org ssh -l root -o 'StrictHostKeyChecking=no' "$minion" 'ps axuww | grep salt | grep -v axuww'
        $SSH bastion-restricted.wmflabs.org ssh -l root -o 'StrictHostKeyChecking=no' "$minion" "dpkg -l | grep salt"
        $SSH bastion-restricted.wmflabs.org ssh -l root -o 'StrictHostKeyChecking=no' "$minion" "cat /etc/issue"
        $SSH bastion-restricted.wmflabs.org ssh -l root -o 'StrictHostKeyChecking=no' "$minion" "ls -lt /var/log/puppet.log"
        $SSH bastion-restricted.wmflabs.org ssh -l root -o 'StrictHostKeyChecking=no' "$minion" "tail -40 /var/log/puppet.log"
done
