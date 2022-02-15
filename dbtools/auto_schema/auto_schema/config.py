import re

from conftool import configuration, kvobject, loader
import requests


class Config():
    def __init__(self, dc=None):
        if not dc:
            self.dcs = ['eqiad', 'codfw']
        else:
            self.dcs[dc]
        self.config = {}
        self._active_dc = None

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
        return self.config[dc]

    def get_dbs(self, section):
        if section.startswith('s'):
            url = 'https://noc.wikimedia.org/conf/dblists/{}.dblist'.format(
                section)
            wikis = [i.strip() for i in requests.get(url).text.split(
                '\n') if not i.startswith('#') and i.strip()]
            return wikis
        else:
            # TODO: Build a way to get dbs of es and pc, etc.
            return []

    def active_dc(self):
        if self._active_dc:
            return self._active_dc

        schema = loader.Schema.from_file('/etc/conftool/schema.yaml')
        kvobject.KVObject.setup(configuration.get('/etc/conftool/config.yaml'))
        config = schema.entities["mwconfig"].query(
            {"name": re.compile("WMFMasterDatacenter")})
        matching = [obj for obj in config]
        self._active_dc = matching[0].val
        return self._active_dc
