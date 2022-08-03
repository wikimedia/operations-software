from ..config import Config
import os
import json


class MockConfig(Config):
    def get_config(self, dc):
        if not self.config.get(dc):
            dir = os.path.dirname(__file__)
            with open(os.path.join(dir, dc + '.json'), 'r') as f:
                self.config[dc] = json.loads(f.read())
        return self.config[dc]
