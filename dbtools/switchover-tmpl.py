import argparse
import re

import requests
from conftool import configuration, kvobject, loader

parser = argparse.ArgumentParser()
parser.add_argument('section', help='Must be the section name in orchestrator')
parser.add_argument('new', help='New primary.')
parser.add_argument('--dc', help='Datacenter. If not set, it picks the active dc')
parser.add_argument('--old', help='Old primary. If not set, it picks the current primary')
parser.add_argument('--ticket', help='Ticket for this switchover. Like T12345')
args = parser.parse_args()


def get_active_dc():
    schema = loader.Schema.from_file('/etc/conftool/schema.yaml')
    kvobject.KVObject.setup(configuration.get('/etc/conftool/config.yaml'))
    config = schema.entities["mwconfig"].query(
        {"name": re.compile("WMFMasterDatacenter")})
    matching = [obj for obj in config]
    return matching[0].val


def get_old_primary(section):
    data = requests.get('https://orchestrator.wikimedia.org/api/cluster/alias/' + section).json()
    return data[0]['ClusterName'].split('.')[0]


section = args.section
affected_wikis = 'https://noc.wikimedia.org/conf/highlight.php?file=dblists/{}.dblist'.format(
    section) if section.startswith('s') else 'TO-DO'
dc = args.dc or get_active_dc()
oldpri = args.old or get_old_primary(section)
oldpri = oldpri.split('.')[0]
newpri = args.new.split('.')[0]
taskid = args.ticket or 'TICKID'

output = """
**When:** During a pre-defined DBA maintenance windows

** Prerequisites **: https://wikitech.wikimedia.org/wiki/MariaDB/Primary_switchover

[] Team calendar invite

**Affected wikis:**: {affected_wikis}

**Checklist:**

NEW primary: {newpri}
OLD primary: {oldpri}

[] Check configuration differences between new and old primary:
```
sudo pt-config-diff --defaults-file /root/.my.cnf h={oldpri}.{dc}.wmnet h={newpri}.{dc}.wmnet
```

**Failover prep:**
[] Silence alerts on all hosts:
```
sudo cookbook sre.hosts.downtime --hours 1 -r "Primary switchover {section} {taskid}" 'A:db-section-{section}'
```
[] Set NEW primary with weight 0 (and depool it from API or vslow/dump groups if it is present).
```
sudo dbctl instance {newpri} set-weight 0
sudo dbctl config commit -m "Set {newpri} with weight 0 {taskid}"
```
[] Topology changes, move all replicas under NEW primary
```
sudo db-switchover --timeout=25 --only-slave-move {oldpri} {newpri}
```
[] Disable puppet on both nodes
```
sudo cumin '{oldpri}* or {newpri}*' 'disable-puppet "primary switchover {taskid}"'
```
[] Merge gerrit puppet change to promote NEW primary: FIXME

**Failover:**
[] Log the failover:
```
!log Starting {section} {dc} failover from {oldpri} to {newpri} - {taskid}
```
[] Set section read-only:
```
sudo dbctl --scope {dc} section {section} ro "Maintenance until 06:15 UTC - {taskid}"
sudo dbctl config commit -m "Set {section} {dc} as read-only for maintenance - {taskid}"
```
[] Check {section} is indeed read-only
[] Switch primaries:
```
sudo db-switchover --skip-slave-move {oldpri} {newpri}
echo "===== {oldpri} (OLD)"; sudo db-mysql {oldpri} -e 'show slave status\\G'
echo "===== {newpri} (NEW)"; sudo db-mysql {newpri} -e 'show slave status\\G'
```

[] Promote NEW primary in dbctl, and remove read-only
```
sudo dbctl --scope {dc} section {section} set-master {newpri}
sudo dbctl --scope {dc} section {section} rw
sudo dbctl config commit -m "Promote {newpri} to {section} primary and set section read-write {taskid}"
```

[] Restart puppet on both hosts:
```
sudo cumin '{oldpri}* or {newpri}*' 'run-puppet-agent -e "primary switchover {taskid}"'
```

**Clean up tasks:**
[] Clean up heartbeat table(s).
```
sudo db-mysql {newpri} heartbeat -e "delete from heartbeat where file like '{oldpri}%';"
```
[] change events for query killer:
```
events_coredb_master.sql on the new primary {newpri}
events_coredb_slave.sql on the new slave {oldpri}
```
[] Update DNS: FIXME
[] Update candidate primary dbctl and orchestrator notes
```
sudo dbctl instance {oldpri} set-candidate-master --section {section} true
sudo dbctl instance {newpri} set-candidate-master --section {section} false
(dborch1001): sudo orchestrator-client -c untag -i {newpri} --tag name=candidate
(dborch1001): sudo orchestrator-client -c tag -i {oldpri} --tag name=candidate
```
[] Check zarcillo was updated
** db-switchover should do this. If it fails, do it manually: https://phabricator.wikimedia.org/P13956
```
sudo db-mysql db1115 zarcillo -e "select * from masters where section = '{section}';"
```
[] (If needed): Depool {oldpri} for maintenance.
```
sudo dbctl instance {oldpri} depool
sudo dbctl config commit -m "Depool {oldpri} {taskid}"
```
[] Apply outstanding schema changes to {oldpri} (if any)
[] Update/resolve this ticket."""

print(output.format(
    section=section,
    oldpri=oldpri,
    newpri=newpri,
    taskid=taskid,
    dc=dc,
    affected_wikis=affected_wikis
))
