import json

import requests


class Config():
    def __init__(self, dc=None):
        if not dc:
            self.dcs = ['eqiad', 'codfw']
        else:
            self.dcs[dc]
        self.config = {}

    def get_replicas(self, section):
        replicas = []
        for dc in self.dcs:
            replicas += self._get_replicas_for_dc(section, dc)
        return replicas

    def get_section_masters(self, section):
        masters = []
        for dc in self.dcs:
            masters.append(self.get_section_master_for_dc(section, dc))
        return masters

    def _get_replicas_for_dc(self, section, dc):
        config = self.get_config(dc)
        section_in_config = 'DEFAULT' if section == 's3' else section
        type_in_config = 'sectionLoads' if section.startswith(
            's') else 'externalLoads'
        return list(config[type_in_config][section_in_config][1].keys())

    def get_section_master_for_dc(self, section, dc):
        config = self.get_config(dc)
        section_in_config = 'DEFAULT' if section == 's3' else section
        type_in_config = 'sectionLoads' if section.startswith(
            's') else 'externalLoads'
        return list(config[type_in_config][section_in_config][0].keys())[0]

    def get_config(self, dc):
        if not self.config.get(dc):
            self.config[dc] = requests.get(
                'https://noc.wikimedia.org/dbconfig/{}.json'.format(dc)).json()
            with open('og_config.json', 'w') as f:
                f.write(json.dumps(self.config))
        return self.config[dc]
