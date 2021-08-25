#!/bin/bash

set -u

if [ $# -eq 0 ]; then
    echo "Usage:"
    echo "    ${0##*/} SECTION DC OLD_PRIMARY NEW_PRIMARY [TASK_ID]"
    exit 0
fi

section=${1:?}; shift
dc=${1:?}; shift
oldpri=${1:?}; shift
newpri=${1:?}; shift
taskid=${1:-TASKID}; shift

# Strip off any domain names
oldpri=${oldpri%%.*}
newpri=${newpri%%.*}

cat << EOF
**When:** FIXME

**Checklist:**
[] Create a task to communicate the chosen date and send an announcement to the community: FIXME
[] Create a calendar entry for the maintenance, invite sre-data-persistence@
[] Add to deployments calendar. E.g.:
\`\`\`
{{Deployment calendar event card
    |when=2021-08-24 23:00 SF
    |length=0.5
    |window=Database primary switchover for s7
    |who={{ircnick|kormat|Stevie Beth Mhaol}}, {{ircnick|marostegui|Manuel 'Early Bird' Arostegui}}
    |what=https://phabricator.wikimedia.org/${taskid}
}}
\`\`\`

NEW primary: ${newpri}
OLD primary: ${oldpri}

[] Check configuration differences between new and old primary:
\`\`\`
sudo pt-config-diff --defaults-file /root/.my.cnf h=${oldpri}.${dc}.wmnet h=${newpri}.${dc}.wmnet
\`\`\`

**Failover prep:**
[] Silence alerts on all hosts:
\`\`\`
sudo cookbook sre.hosts.downtime --hours 1 -r "Primary switchover ${section} ${taskid}" 'A:db-section-${section}'
\`\`\`
[] Set NEW primary with weight 0
\`\`\`
sudo dbctl instance ${newpri} set-weight 0
sudo dbctl config commit -m "Set ${newpri} with weight 0 ${taskid}"
\`\`\`
[] Topology changes, move all replicas under NEW primary
\`\`\`
sudo db-switchover --timeout=15 --only-slave-move ${oldpri} ${newpri}
\`\`\`
[] Disable puppet on both nodes
\`\`\`
sudo cumin '${oldpri}* or ${newpri}*' 'disable-puppet "primary switchover ${taskid}"'
\`\`\`
[] Merge gerrit puppet change to promote NEW primary: FIXME

**Failover:**
[] Log the failover:
\`\`\`
!log Starting ${section} ${dc} failover from ${oldpri} to ${newpri} - ${taskid}
\`\`\`
[] Set section read-only:
\`\`\`
sudo dbctl --scope ${dc} section ${section} ro "Maintenance until 05:15 UTC - ${taskid}"
sudo dbctl config commit -m "Set ${section} ${dc} as read-only for maintenance - ${taskid}"
\`\`\`
[] Check ${section} is indeed read-only
[] Switch primaries:
\`\`\`
sudo db-switchover --skip-slave-move ${oldpri} ${newpri}
echo "===== ${oldpri} (OLD)"; sudo mysql.py -h ${oldpri} -e 'show slave status\G'
echo "===== ${newpri} (NEW)"; sudo mysql.py -h ${newpri} -e 'show slave status\G'
\`\`\`

[] Promote NEW primary in dbctl, and remove read-only
\`\`\`
sudo dbctl --scope ${dc} section ${section} set-master ${newpri}
sudo dbctl --scope ${dc} section ${section} rw
sudo dbctl config commit -m "Promote ${newpri} to ${section} primary and set section read-write ${taskid}"
\`\`\`

[] Restart puppet on both hosts:
\`\`\`
sudo cumin '${oldpri}* or ${newpri}*' 'run-puppet-agent -e "primary switchover ${taskid}"'
\`\`\`

**Clean up tasks:**
[] Clean up heartbeat table(s).
[] change events for query killer:
\`\`\`
events_coredb_master.sql on the new primary ${newpri}
events_coredb_slave.sql on the new slave ${oldpri}
\`\`\`
[] Update DNS: FIXME
[] Update candidate primary dbctl notes
\`\`\`
sudo dbctl instance ${oldpri} set-candidate-master --section ${section} true
sudo dbctl instance ${newpri} set-candidate-master --section ${section} false
\`\`\`
[] Check tendril was updated
[] Check zarcillo was updated
** db-switchover should do this. If it fails, do it manually: https://phabricator.wikimedia.org/P13956
[] Depool OLD primary, as it's running 10.1, replicating from a 10.4 primary
\`\`\`
sudo dbctl instance ${oldpri} depool
sudo dbctl config commit -m "Depool ${oldpri} until it's reimaged to buster ${taskid}"
\`\`\`
[] Apply outstanding schema changes to ${oldpri} (if any)
[] Update/resolve this ticket.
EOF
