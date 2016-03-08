use ops;

SET session sql_log_bin=0;

DROP EVENT `wmf_slave_overload`;
DROP EVENT `wmf_slave_purge`;
DROP EVENT `wmf_slave_wikiuser_sleep`;
DROP EVENT `wmf_slave_wikiuser_slow`;

DELIMITER //

CREATE DEFINER=`root`@`localhost` EVENT `wmf_slave_overload` ON SCHEDULE EVERY 10 SECOND STARTS '2014-08-13 00:00:01' ON COMPLETION NOT PRESERVE ENABLE DO begin

        declare sid int;
        declare all_done int default 0;
        declare thread_id bigint default null;
        declare thread_query varchar(100);
        declare active_count bigint default null;

        declare active_queries cursor for
            select ps.id, substring(info,1,100)
            from information_schema.processlist ps
            where ps.command = 'Query'
                and ps.user = 'wikiuser'
                and ps.time between 10 and 1000000
                and ps.info is not null
                and lower(ps.info) regexp '^[[:space:]]*select'
                and not lower(ps.info) regexp 'wikiexporter'
                and not lower(ps.info) regexp 'master_pos_wait'
            order by ps.time desc
            limit 100;

        declare continue handler for not found set all_done = 1;

        if (get_lock('wmf_slave_overload', 1) = 0) then
            signal sqlstate value '45000' set message_text = 'get_lock';
        end if;

        set sid := @@server_id;
        set session sql_log_bin := 0;

        set active_count := (
            select count(ps.id)
            from information_schema.processlist ps
            where ps.command = 'Query'
                and ps.info is not null
        );


        if (active_count is not null and active_count > 300) then

            set all_done = 0;
            open active_queries;

            repeat fetch active_queries into thread_id, thread_query;

                if (thread_id is not null) then

                    kill thread_id;

                    insert into event_log values (sid, now(), 'wmf_slave_overload (300)',
                        concat('kill ',thread_id,'; ',thread_query)
                    );

                end if;

                until all_done
            end repeat;

            close active_queries;

        end if;

        select 1 from (select 1) as t;

        do release_lock('wmf_slave_overload');

    end
//

CREATE DEFINER=`root`@`localhost` EVENT `wmf_slave_purge` ON SCHEDULE EVERY 15 MINUTE STARTS '2014-08-13 00:00:00' ON COMPLETION NOT PRESERVE ENABLE DO begin
  declare sid int;

  set session sql_log_bin := 0;

  set sid := @@server_id;

  delete from event_log where stamp < now() - interval 1 day and server_id = sid;

    end
//

CREATE DEFINER=`root`@`localhost` EVENT `wmf_slave_wikiuser_sleep` ON SCHEDULE EVERY 30 SECOND STARTS '2014-08-13 00:00:05' ON COMPLETION NOT PRESERVE ENABLE DO begin

        declare sid int;
        declare all_done int default 0;
        declare thread_id bigint default null;

        declare threads_sleeping cursor for
            select ps.id
            from information_schema.processlist ps
            where ps.command = 'Sleep'
                and ps.user = 'wikiuser'
                and ps.time between 300 and 1000000
                and ps.info is null
            order by ps.time desc;

        declare continue handler for not found set all_done = 1;

        if (get_lock('wmf_slave_wikiuser_sleep', 1) = 0) then
            signal sqlstate value '45000' set message_text = 'get_lock';
        end if;

        set session sql_log_bin := 0;
        set sid := @@server_id;

        set all_done = 0;
        open threads_sleeping;

        repeat fetch threads_sleeping into thread_id;

            if (thread_id is not null) then

                kill thread_id;

                insert into event_log values (sid, now(), 'wmf_slave_wikiuser_sleep',
                    concat('kill ',thread_id)
                );

            end if;

            until all_done
        end repeat;

        close threads_sleeping;

        select 1 from (select 1) as t;

        do release_lock('wmf_slave_wikiuser_sleep');

    end
//

CREATE DEFINER=`root`@`localhost` EVENT `wmf_slave_wikiuser_slow` ON SCHEDULE EVERY 30 SECOND STARTS '2014-08-13 00:00:03' ON COMPLETION NOT PRESERVE ENABLE DO begin

        declare sid int;
        declare all_done int default 0;
        declare thread_id bigint default null;
        declare thread_query varchar(100);

        declare slow_queries cursor for
            select ps.id, substring(info,1,100)
            from information_schema.processlist ps
            where ps.command = 'Query'
                and ps.user = 'wikiuser'
                and ps.info is not null
                and lower(ps.info) regexp '^[[:space:]]*select'
                and not lower(ps.info) regexp 'wikiexporter'
                and not lower(ps.info) regexp 'master_pos_wait'
                and (
                    ps.time between 300 and 1000000
                    or (ps.time between 30 and 1000000 and ps.info like '%SpecialWhatLinksHere%')
                )
            order by ps.time desc;

        declare continue handler for not found set all_done = 1;

        set session sql_log_bin := 0;
        set sid := @@server_id;

        if (get_lock('wmf_slave_wikiuser_slow', 1) = 0) then
            signal sqlstate value '45000' set message_text = 'get_lock';
        end if;

        set all_done = 0;
        open slow_queries;

        repeat fetch slow_queries into thread_id, thread_query;

            if (thread_id is not null) then

                kill thread_id;

                insert into event_log values (sid, now(), 'wmf_slave_wikiuser_slow',
                    concat('kill ',thread_id, '; ',thread_query)
                );

            end if;

            until all_done
        end repeat;

        close slow_queries;

        select 1 from (select 1) as t;

        do release_lock('wmf_slave_wikiuser_slow');

    end
//

DELIMITER ;
