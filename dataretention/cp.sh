basedir="/srv/audits/retention"
scriptsdir="${basedir}/scripts"
libdir="${scriptsdir}/retention"
pythondir="/usr/lib/python2.7/site-packages"
pythonlibdir="${pythondir}/clouseau/retention"
configsdir="${basedir}/configs"
saltmodsdir="/srv/salt/_modules"

mkdir -p "$pythonlibdir"

libfiles="__init__.py cliutils.py completion.py \
  config.py fileinfo.py fileutils.py ignores.py \
  magic.py rule.py ruleutils.py saltclientplus.py status.py utils.py \
  locallogaudit.py localfileaudit.py localhomeaudit.py \
  localusercfgrabber.py localexaminer.py"
cd retention; cp $libfiles "$pythonlibdir"; cd ..

files="__init__.py cli.py remoteexaminer.py runner.py \
  remotefileauditor.py remotelogauditor.py \
  remotehomeauditor.py  fileutils.py \
  remoteusercfgrabber.py"
cd retention; cp $files "$libdir"; cd ..

cp data_auditor.py rulestore.py data_auditor_run.sh "$scriptsdir"
cd retention; cp config.yaml global_ignored.yaml perhost_ignored.yaml "$configsdir"; cd ..
cd retention; cp retentionaudit.py "$saltmodsdir"; cd ..



