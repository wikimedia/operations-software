import os
COMPILE_SCRIPT = '/vagrant/shell/compile'
FETCH_CHANGE = '/vagrant/shell/prepare_change'
DIFF_SCRIPT = '/vagrant/shell/differ'
NODE_DIR = '/vagrant/external/var/yaml/node'
RUBY_VERSION = '1.8.7-p374'
PUPPET_VERSIONS = [('2.7', 'production'), ('3', 'production')]
OUTPUT_DIR = '/vagrant/output'
COMPILE_OUTPUT_DIR = os.path.join(OUTPUT_DIR, 'compiled')
DIFF_DIR = os.path.join(OUTPUT_DIR, 'diff')
HTML_DIR = os.path.join(OUTPUT_DIR, 'html')
