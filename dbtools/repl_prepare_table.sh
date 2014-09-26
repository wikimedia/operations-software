#!/bin/bash

set -e

usage() {
    echo $0 --host=... --db=... --table...
    exit 1
}

user="root"
host=""
port="3306"
dblist=()
db=""
tbl=""

for var in "$@"; do

    if [[ "$var" =~ ^--host=(.+) ]]; then
        host="${BASH_REMATCH[1]}"
    fi

    if [[ "$var" =~ ^--port=(.+) ]]; then
        port="${BASH_REMATCH[1]}"
    fi

    if [[ "$var" =~ ^--user=(.+) ]]; then
        user="${BASH_REMATCH[1]}"
    fi

    if [[ "$var" =~ ^--db=(.+) ]]; then
        db="${BASH_REMATCH[1]}"
    fi

    if [[ "$var" =~ ^--table=(.+) ]]; then
        tbl="${BASH_REMATCH[1]}"
    fi

done

[ "$db"   ] || usage
[ "$tbl"  ] || usage
[ "$host" ] || usage

my="mysql -h $host -P $port -u $user --skip-column-names"
nolog="set session sql_log_bin = 0;"

sql="select engine from information_schema.tables where table_schema = '$db' and table_name = '$tbl'"
engine=$($my -e "$sql")

sql="select column_name from information_schema.columns"
sql="$sql where table_schema = '$db' and table_name = '$tbl'"
sql="$sql and column_name = 'repl_uuid' and column_key in ('UNI', 'PRI')"
col=$($my -e "$sql")

if [[ ! "$col" =~ 'repl_uuid' ]]; then

    sql="select column_name from information_schema.columns "
    sql="$sql where table_schema = '$db' and table_name = '$tbl' and column_name = 'repl_uuid'"
    oldcol=$($my -e "$sql")

    if [[ ! "$oldcol" =~ 'repl_uuid' ]]; then
        alter="${nolog} alter"
        if [[ "$engine" =~ ^InnoDB$ ]]; then
            alter="${alter} online"
        fi
        $my -e "${alter} table $tbl add repl_uuid binary(16) default null" $db
    fi
fi

filter=""
sql="select concat('set new.', f.column_name, '=', f.empty_string, ';')"
sql="$sql from repl_filter f join information_schema.columns c"
sql="$sql on c.table_schema = database() and c.table_name = f.table_name and c.column_name = f.column_name"
sql="$sql where f.table_name = '${tbl}'"
for row in $($my -e "$sql" $db); do
    filter="$filter $row"
done

$my $db <<EOD
${nolog}
drop trigger if exists ${tbl}_ins;
drop trigger if exists ${tbl}_upd;
drop trigger if exists ${tbl}_del;
delimiter ;;
create trigger ${tbl}_ins before insert on ${tbl} for each row
    begin
        set new.repl_uuid = unhex(replace(uuid(),'-',''));
        ${filter}
        insert into repl_records (record_uuid, record_stamp, table_md5)
            values (new.repl_uuid, now(), unhex(md5("${tbl}")));
    end ;;
EOD

sql="update $tbl set repl_uuid = unhex(replace(uuid(),'-','')) where repl_uuid is null"
$my -e "${nolog} ${sql}" $db

if [[ ! "$col" =~ 'repl_uuid' ]]; then
    sql="alter ignore table $tbl"
    sql="$sql modify repl_uuid binary(16) not null default 0,"
    sql="$sql add unique index (repl_uuid)"
    $my -e "${nolog} ${sql}" $db
fi

$my $db <<EOD
${nolog}
delimiter ;;
create trigger ${tbl}_upd before update on ${tbl} for each row
    begin
        ${filter}
        insert into repl_records (record_uuid, record_stamp, table_md5)
            values (old.repl_uuid, now(), unhex(md5("${tbl}")));
    end ;;
create trigger ${tbl}_del after delete on ${tbl} for each row
    begin
        insert into repl_records (record_uuid, record_stamp, table_md5)
            values (old.repl_uuid, now(), unhex(md5("${tbl}")));
    end ;;
EOD

sql="replace into repl_tables (table_name) values ('${tbl}')"
$my -e "${nolog} ${sql}" $db
