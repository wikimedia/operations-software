import os
from setuptools import setup
import glob


def read(files):
    content = ''
    for filename in files:
        content = content + "\n" + open(
            os.path.join(os.path.dirname(__file__), filename)).read()
    return content


def get_files(path, extension=None):
    if extension is None:
        return glob.glob(path + '*')
    else:
        return glob.glob(path + '*.' + extension)

setup(
    name="clouseau",
    version="0.0.1",
    author="Ariel T. Glenn",
    author_email="ariel@wikimedia.org",
    description=("Auditing scripts and libraries"),
    license="GPLv2",
    url="https://phabricator.wikimedia.org/r/project/something/retention",
    packages=['clouseau', 'clouseau.retention', 'clouseau.retention.local',
              'clouseau.retention.remote', 'clouseau.retention.utils', 'tests'],
    data_files=[('/srv/audits/retention/scripts', get_files('scripts/retention/wmf/', 'sh')),
                ('/srv/audits/retention/scripts', get_files('scripts/retention/', 'py')),
                ('/srv/audits/retention/configs', get_files('docs/retention/')),
                ('/srv/salt/_modules', get_files('salt/retention/', 'py'))],
    long_description=read(['README.txt', 'README_retention.txt']),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)",
    ],
)
