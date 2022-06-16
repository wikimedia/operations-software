use ops;

SET session sql_log_bin=0;

DROP EVENT IF EXISTS `wmf_slave_overload`;
DROP EVENT IF EXISTS `wmf_slave_purge`;
DROP EVENT IF EXISTS `wmf_slave_wikiuser_sleep`;
DROP EVENT IF EXISTS `wmf_slave_wikiuser_slow`;
DROP EVENT IF EXISTS `wmf_master_purge`;
DROP EVENT IF EXISTS `wmf_master_wikiuser_sleep`;

DELIMITER //

CREATE DEFINER=`root`@`localhost` EVENT `wmf_master_purge` ON SCHEDULE EVERY 15 MINUTE STARTS '2014-08-26 00:00:00' ON COMPLETION NOT PRESERVE ENABLE DO begin

        declare sid int;

        set sid := @@server_id;
        set @@session.sql_log_bin = 0;

        delete from event_log where stamp < now() - interval 1 day and server_id = sid;

    end
//

CREATE DEFINER=`root`@`localhost` EVENT `wmf_master_wikiuser_sleep` ON SCHEDULE EVERY 30 SECOND STARTS '2014-08-26 00:00:05' ON COMPLETION NOT PRESERVE ENABLE DO begin

        declare sid int;
        declare all_done int default 0;
        declare thread_id bigint default null;

        declare threads_sleeping cursor for
            select ps.id
            from information_schema.processlist ps
            where ps.command = 'Sleep'
                and ps.user = 'wikiuser202206'
                and ps.time between 300 and 1000000
                and ps.info is null
            order by ps.time desc;

        declare continue handler for not found set all_done = 1;

        if (get_lock('wmf_master_wikiuser_sleep', 1) = 0) then
            signal sqlstate value '45000' set message_text = 'get_lock';
        end if;

        set sid := @@server_id;
        set @@session.sql_log_bin = 0;

        set all_done = 0;
        open threads_sleeping;

        repeat fetch threads_sleeping into thread_id;

            if (thread_id is not null) then

                kill thread_id;

                insert into event_log values (sid, now(), 'wmf_master_wikiuser_sleep',
                    concat('kill ',thread_id)
                );

            end if;

            until all_done
        end repeat;

        close threads_sleeping;

        select 1 from (select 1) as t;

        do release_lock('wmf_master_wikiuser_sleep');

    end
//

DELIMITER ;
