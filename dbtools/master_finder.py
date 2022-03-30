import argparse
import json

import requests

parser = argparse.ArgumentParser()
parser.add_argument('section', help='Must be the section name in orchestrator')
args = parser.parse_args()
data_ = requests.get(
    'https://orchestrator.wikimedia.org/api/cluster/alias/' +
    args.section).json()
db_data = []
for db in data_:
    analyzed_db = {}
    if db['Key']['Hostname'].startswith('dbstore'):
        # let's not promote dbstore to master
        continue
    if db['MasterKey']['Hostname'] + ':' + \
            str(db['MasterKey']['Port']) != db['ClusterName']:
        # not a direct replica
        continue
    if db['Replicas']:
        analyzed_db['has replicas'] = True
    name = db['Key']['Hostname'] + ':' + str(db['Key']['Port'])
    analyzed_db['name'] = name
    if db['Problems']:
        analyzed_db['problems'] = db['Problems']
    if db['Key']['Port'] != 3306:
        analyzed_db['multiinstace'] = True
    analyzed_db['binlog format'] = db['Binlog_format']
    if db['ClusterName'][2] != db['Key']['Hostname'][2]:
        analyzed_db['different dc'] = True
    analyzed_db['position'] = '{}:{}'.format(
        db['ExecBinlogCoordinates']['LogFile'],
        db['ExecBinlogCoordinates']['LogPos'])
    db_data.append(analyzed_db)

db_data = sorted(db_data, key=lambda i: i['position'], reverse=True)
print('Ordered based on log position, the freshest first:')
for db in db_data:
    if db.get('binlog format') == 'STATEMENT' and not db.get(
            'has replicas') and not db.get('different dc'):
        print('\033[32m' + json.dumps(db) + '\033[0m')
    else:
        print(json.dumps(db))
