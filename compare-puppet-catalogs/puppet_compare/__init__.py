from puppet_compare import app_defaults


class StubFlask(object):
    # stub class that allows to use app.config as a repository of data while
    # the web part of the app is not ready
    config = {}

app = StubFlask()
for k, v in app_defaults.__dict__.items():
    if not k.startswith('__'):
        app.config[k] = v
