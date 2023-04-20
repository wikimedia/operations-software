import pymysql.cursors


class Db(object):
    def __init__(self, host, db_name):
        self.host = host
        self.db_name = db_name

    def run_sql(self, sql):
        return self.host.run_sql('use {}; '.format(self.db_name) + sql)

    def get_columns(self, table_name, db=None):
        db = db or self.db_name
        sql = "select * from information_schema.columns where " + \
            "table_schema='{}' and table_name='{}';".format(db, table_name)
        connection = pymysql.connect(
            host=self.host.fqn,
            port=self.host.port,
            read_default_file='/root/.my.cnf',
            cursorclass=pymysql.cursors.DictCursor)
        columns = {}
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchall()
                for row in result:
                    columns[row['COLUMN_NAME']] = row
        return columns

    def get_indexes(self, table_name, db=None):
        sql = "show index from {};".format(table_name)
        connection = pymysql.connect(
            host=self.host.fqn,
            port=self.host.port,
            database=db or self.db_name,
            read_default_file='/root/.my.cnf',
            cursorclass=pymysql.cursors.DictCursor)
        indexes = {}
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchall()
                for row in result:
                    if row['Key_name'] not in indexes:
                        indexes[row['Key_name']] = {
                            'columns': [],
                            'unique': int(row['Non_unique']) == 0
                        }
                    indexes[row['Key_name']]['columns'].append(row['Column_name'])

        return indexes
