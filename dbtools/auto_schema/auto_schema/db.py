class Db(object):
    def __init__(self, host, db_name):
        self.host = host
        self.db_name = db_name

    def run_sql(self, sql):
        return self.host.run_sql('use {}; '.format(self.db_name) + sql)

    # TODO: Add functions such as has_index, has_column, ...
