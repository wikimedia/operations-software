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
**When:** During a pre-defined DBA maintenance windows

**Affected wikis:**: TO-DO

**Checklist:**

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
echo "===== ${oldpri} (OLD)"; sudo db-mysql ${oldpri} -e 'show slave status\G'
echo "===== ${newpri} (NEW)"; sudo db-mysql ${newpri} -e 'show slave status\G'
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
[] Update candidate primary dbctl and orchestrator notes
\`\`\`
sudo dbctl instance ${oldpri} set-candidate-master --section ${section} true
sudo dbctl instance ${newpri} set-candidate-master --section ${section} false
(dborch1001): sudo orchestrator-client -c untag -i ${newpri} --tag name=candidate
(dborch1001): sudo orchestrator-client -c tag -i ${oldpri} --tag name=candidate
\`\`\`
[] Check zarcillo was updated
** db-switchover should do this. If it fails, do it manually: https://phabricator.wikimedia.org/P13956
[] (If needed): Depool ${oldpri} for maintenance.
\`\`\`
sudo dbctl instance ${oldpri} depool
sudo dbctl config commit -m "Depool ${oldpri} ${taskid}"
\`\`\`
[] Apply outstanding schema changes to ${oldpri} (if any)
[] Update/resolve this ticket.
EOF
