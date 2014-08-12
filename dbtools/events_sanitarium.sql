-- Events for sanitarium db10(53|54|57)

set @cache_sql_log_bin := @@session.sql_log_bin;
set @@session.sql_log_bin = 1;

set @cache_event_scheduler := @@global.event_scheduler;
set @@global.event_scheduler = 0;

create database if not exists ops;

use ops;

-- Remember, table is replicated!
-- https://wikitech.wikimedia.org/wiki/MariaDB#Schema_Changes

create table if not exists event_log (
  server_id int unsigned  not null,
  stamp     datetime      not null,
  event     varchar(100)  not null,
  content   varchar(1024) not null,
  index server_stamp (server_id, stamp)
) engine=innodb default charset=binary;

create database if not exists information_schema_p;

use information_schema_p;

create table if not exists schemata (
  catalog_name varchar(512) not null default '',
  schema_name varchar(64) not null default '',
  default_character_set_name varchar(32) not null default '',
  default_collation_name varchar(32) not null default '',
  sql_path varchar(512) default null,
  primary key (schema_name)
) engine=innodb default charset=binary;

create table if not exists tables (
  table_catalog varchar(512) not null default '',
  table_schema varchar(64) not null default '',
  table_name varchar(64) not null default '',
  table_type varchar(64) not null default '',
  engine varchar(64) default null,
  version bigint(21) unsigned default null,
  row_format varchar(10) default null,
  table_rows bigint(21) unsigned default null,
  avg_row_length bigint(21) unsigned default null,
  data_length bigint(21) unsigned default null,
  max_data_length bigint(21) unsigned default null,
  index_length bigint(21) unsigned default null,
  data_free bigint(21) unsigned default null,
  auto_increment bigint(21) unsigned default null,
  create_time datetime default null,
  update_time datetime default null,
  check_time datetime default null,
  table_collation varchar(32) default null,
  checksum bigint(21) unsigned default null,
  create_options varchar(255) default null,
  table_comment varchar(2048) not null default '',
  primary key (table_schema, table_name),
  key (table_name)
) engine=innodb default charset=binary;

use ops;

-- Avoid replicating event DDL. Labs events should only be created on labsdb
-- though they may rely on replicated tables like event_log.

set @@session.sql_log_bin = 0;

delimiter ;;

-- Housekeeping

drop event if exists wmf_labs_purge;;

create event wmf_labs_purge

    on schedule every 15 minute starts date(now())

    do begin

        declare sid int;

        set sid := @@server_id;

        delete from event_log where stamp < now() - interval 1 day and server_id = sid;

    end ;;

drop event if exists wmf_information_schema_p;;

create event wmf_information_schema_p

    on schedule every 1 hour starts date(now()) + interval 0 second

    do begin

      declare all_done int default 0;
      declare schema_string varchar(100);

      declare schema_list cursor for
          select schema_name
          from information_schema.schemata
          where (schema_name like '%wik%' or schema_name like '%auth%')
          and schema_name not like '%\_p'
          and schema_name <> 'l10nwiki'
          order by schema_name;

      declare continue handler for not found set all_done = 1;

      if (get_lock('wmf_information_schema_p', 1) = 0) then
          signal sqlstate value '45000' set message_text = 'get_lock';
      end if;

      set all_done = 0;
      open schema_list;

      repeat fetch schema_list into schema_string;

        if (all_done = 0 and schema_string is not null) then

          set session binlog_format = statement;

          delete from information_schema_p.schemata
            where schema_name = schema_string;

          delete from information_schema_p.tables
            where table_schema = schema_string;

          set session binlog_format = row;

          insert ignore into information_schema_p.schemata select
            catalog_name,
            schema_name,
            default_character_set_name,
            default_collation_name,
            sql_path
            from information_schema.schemata
            where schema_name = schema_string;

          insert ignore into information_schema_p.tables select
            table_catalog,
            table_schema,
            table_name,
            table_type,
            engine,
            version,
            row_format,
            table_rows,
            avg_row_length,
            data_length,
            max_data_length,
            index_length,
            data_free,
            auto_increment,
            create_time,
            update_time,
            check_time,
            table_collation,
            checksum,
            create_options,
            table_comment
            from information_schema.tables
            where table_schema = schema_string
            and table_type = 'BASE TABLE';

        end if;

        until all_done
      end repeat;

      close schema_list;

      -- https://mariadb.atlassian.net/browse/MDEV-4602
      select 1 from (select 1) as t;

      do release_lock('wmf_information_schema_p');

    end ;;

delimiter ;

set @@session.sql_log_bin = @cache_sql_log_bin;
set @@global.event_scheduler = @cache_event_scheduler;
