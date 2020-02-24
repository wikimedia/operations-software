-- bgwiki

      select       1 as n, count(rev_user) from bgwiki.revision where rev_user  < 1
union select   10000 as n, count(rev_user) from bgwiki.revision where rev_user >= 1      and rev_user < 10000
union select  100000 as n, count(rev_user) from bgwiki.revision where rev_user >= 10000  and rev_user < 100000
union select 1000000 as n, count(rev_user) from bgwiki.revision where rev_user >= 100000 and rev_user < 1000000
union select 2000000 as n, count(rev_user) from bgwiki.revision where rev_user >= 1000000;

-- results on 2017-09-20:
-- +---------+-----------------+
-- | n       | count(rev_user) |
-- +---------+-----------------+
-- |       1 |         1009270 |
-- |   10000 |         2372980 |
-- |  100000 |         3134647 |
-- | 1000000 |         1188335 |
-- | 2000000 |               0 |
-- +---------+-----------------+
-- 5 rows in set (2.39 sec)

-- Not needed anymore T233625
-- ALTER TABLE bgwiki.logging
--   DROP PRIMARY KEY,
--   ADD PRIMARY KEY (log_id, log_user)
--   PARTITION BY RANGE (log_user) (
--   PARTITION p1 VALUES LESS THAN (1),
--   PARTITION p10000 VALUES LESS THAN (10000),
--   PARTITION p50000 VALUES LESS THAN (50000),
--   PARTITION p100000 VALUES LESS THAN (100000),
--   PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

-- Not needed anymore T239453
-- ALTER TABLE bgwiki.revision
--   DROP PRIMARY KEY,
--   ADD PRIMARY KEY (rev_id, rev_user),
--   DROP INDEX user_timestamp,
--   ADD INDEX user_timestamp (rev_user, rev_timestamp, rev_id),
--   DROP KEY rev_timestamp,
--   ADD KEY rev_timestamp (rev_timestamp, rev_id),
--   DROP KEY page_timestamp,
--   ADD KEY page_timestamp (rev_page, rev_timestamp, rev_id),
--   DROP KEY usertext_timestamp,
--   ADD KEY usertext_timestamp (rev_user_text, rev_timestamp, rev_id),
--   DROP KEY page_user_timestamp,
--   ADD KEY page_user_timestamp (rev_page, rev_user, rev_timestamp, rev_id),
--   DROP KEY rev_page_id,
--   ADD KEY rev_page_id (rev_page, rev_id)
--   PARTITION BY RANGE (rev_user) (
--   PARTITION p1 VALUES LESS THAN (1),
--   PARTITION p10000 VALUES LESS THAN (10000),
--   PARTITION p50000 VALUES LESS THAN (50000),
--   PARTITION p100000 VALUES LESS THAN (100000),
--   PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );
-- 
-- cswiki

      select       1 as n, count(rev_user) from cswiki.revision where rev_user  < 1
union select   10000 as n, count(rev_user) from cswiki.revision where rev_user >= 1      and rev_user < 10000
union select  100000 as n, count(rev_user) from cswiki.revision where rev_user >= 10000  and rev_user < 100000
union select 1000000 as n, count(rev_user) from cswiki.revision where rev_user >= 100000 and rev_user < 1000000
union select 2000000 as n, count(rev_user) from cswiki.revision where rev_user >= 1000000;

-- results on 2017-09-20:
-- +---------+-----------------+
-- | n       | count(rev_user) |
-- +---------+-----------------+
-- |       1 |         1380210 |
-- |   10000 |         4310041 |
-- |  100000 |         5212679 |
-- | 1000000 |         3611541 |
-- | 2000000 |               0 |
-- +---------+-----------------+
-- 5 rows in set (4.06 sec)

-- Not needed anymore T233625
-- ALTER TABLE cswiki.logging
--  DROP PRIMARY KEY,
--  ADD PRIMARY KEY (log_id, log_user)
--  PARTITION BY RANGE (log_user) (
--  PARTITION p1 VALUES LESS THAN (1),
--  PARTITION p10000 VALUES LESS THAN (10000),
--  PARTITION p100000 VALUES LESS THAN (100000),
--  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

-- Not needed anymore T239453
-- ALTER TABLE cswiki.revision
--   DROP PRIMARY KEY,
--   ADD PRIMARY KEY (rev_id, rev_user),
--   DROP INDEX user_timestamp,
--   ADD INDEX user_timestamp (rev_user, rev_timestamp, rev_id),
--   DROP KEY rev_timestamp,
--   ADD KEY rev_timestamp (rev_timestamp, rev_id),
--   DROP KEY page_timestamp,
--   ADD KEY page_timestamp (rev_page, rev_timestamp, rev_id),
--   DROP KEY usertext_timestamp,
--   ADD KEY usertext_timestamp (rev_user_text, rev_timestamp, rev_id),
--   DROP KEY page_user_timestamp,
--   ADD KEY page_user_timestamp (rev_page, rev_user, rev_timestamp, rev_id),
--   DROP KEY rev_page_id,
--   ADD KEY rev_page_id (rev_page, rev_id)
--   PARTITION BY RANGE (rev_user) (
--   PARTITION p1 VALUES LESS THAN (1),
--   PARTITION p10000 VALUES LESS THAN (10000),
--   PARTITION p100000 VALUES LESS THAN (100000),
--   PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

-- enwikiquote

      select       1 as n, count(rev_user) from enwikiquote.revision where rev_user  < 1
union select   10000 as n, count(rev_user) from enwikiquote.revision where rev_user >= 1      and rev_user < 10000
union select  100000 as n, count(rev_user) from enwikiquote.revision where rev_user >= 10000  and rev_user < 100000
union select 1000000 as n, count(rev_user) from enwikiquote.revision where rev_user >= 100000 and rev_user < 1000000
union select 2000000 as n, count(rev_user) from enwikiquote.revision where rev_user >= 1000000;

-- results on 2017-09-20:
-- +---------+-----------------+
-- | n       | count(rev_user) |
-- +---------+-----------------+
-- |       1 |          828991 |
-- |   10000 |          478794 |
-- |  100000 |          352831 |
-- | 1000000 |          326074 |
-- | 2000000 |          127378 |
-- +---------+-----------------+
-- 5 rows in set (0.74 sec)

-- Not needed anymore T233625
-- ALTER TABLE enwikiquote.logging
--   DROP PRIMARY KEY,
--   ADD PRIMARY KEY (log_id, log_user)
--   PARTITION BY RANGE (log_user) (
--   PARTITION p1 VALUES LESS THAN (1),
--   PARTITION p10000 VALUES LESS THAN (10000),
--   PARTITION p100000 VALUES LESS THAN (100000),
--   PARTITION p200000 VALUES LESS THAN (200000),
--   PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

-- Not needed anymore T239453
-- ALTER TABLE enwikiquote.revision
--   DROP PRIMARY KEY,
--   ADD PRIMARY KEY (rev_id, rev_user),
--   DROP INDEX user_timestamp,
--   ADD INDEX user_timestamp (rev_user, rev_timestamp, rev_id),
--   DROP KEY rev_timestamp,
--   ADD KEY rev_timestamp (rev_timestamp, rev_id),
--   DROP KEY page_timestamp,
--   ADD KEY page_timestamp (rev_page, rev_timestamp, rev_id),
--   DROP KEY usertext_timestamp,
--   ADD KEY usertext_timestamp (rev_user_text, rev_timestamp, rev_id),
--   DROP KEY page_user_timestamp,
--   ADD KEY page_user_timestamp (rev_page, rev_user, rev_timestamp, rev_id),
--   DROP KEY rev_page_id,
--   ADD KEY rev_page_id (rev_page, rev_id)
--   PARTITION BY RANGE (rev_user) (
--   PARTITION p1 VALUES LESS THAN (1),
--   PARTITION p10000 VALUES LESS THAN (10000),
--   PARTITION p100000 VALUES LESS THAN (100000),
--   PARTITION p200000 VALUES LESS THAN (200000),
--   PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );
-- 
-- enwiktionary

      select       1 as n, count(rev_user) from enwiktionary.revision where rev_user  < 1
union select   10000 as n, count(rev_user) from enwiktionary.revision where rev_user >= 1       and rev_user <  10000
union select   20000 as n, count(rev_user) from enwiktionary.revision where rev_user >= 10000   and rev_user <  20000
union select   30000 as n, count(rev_user) from enwiktionary.revision where rev_user >= 20000   and rev_user <  30000
union select   40000 as n, count(rev_user) from enwiktionary.revision where rev_user >= 30000   and rev_user <  40000
union select   50000 as n, count(rev_user) from enwiktionary.revision where rev_user >= 40000   and rev_user <  50000
union select  100000 as n, count(rev_user) from enwiktionary.revision where rev_user >= 50000   and rev_user < 100000
union select  200000 as n, count(rev_user) from enwiktionary.revision where rev_user >= 100000  and rev_user < 200000
union select  300000 as n, count(rev_user) from enwiktionary.revision where rev_user >= 200000  and rev_user < 300000
union select  400000 as n, count(rev_user) from enwiktionary.revision where rev_user >= 300000  and rev_user < 400000
union select  500000 as n, count(rev_user) from enwiktionary.revision where rev_user >= 400000  and rev_user < 500000
union select 1000000 as n, count(rev_user) from enwiktionary.revision where rev_user >= 500000  and rev_user < 1000000
union select 2000000 as n, count(rev_user) from enwiktionary.revision where rev_user >= 1000000 and rev_user < 2000000
union select 3000000 as n, count(rev_user) from enwiktionary.revision where rev_user >= 3000000;

-- results on 2017-09-20:
-- +---------+-----------------+
-- | n       | count(rev_user) |
-- +---------+-----------------+
-- |       1 |         1291874 |
-- |   10000 |         3731249 |
-- |   20000 |          974370 |
-- |   30000 |         4825233 |
-- |   40000 |         2648562 |
-- |   50000 |         6968329 |
-- |  100000 |         2666343 |
-- |  200000 |          600025 |
-- |  300000 |         4157888 |
-- |  400000 |        11473520 |
-- |  500000 |         1501967 |
-- | 1000000 |         1316460 |
-- | 2000000 |         1612034 |
-- | 3000000 |          936717 |
-- +---------+-----------------+
-- 14 rows in set (11.07 sec)

-- Not needed anymore T233625
-- ALTER TABLE enwiktionary.logging
--   DROP PRIMARY KEY,
--   ADD PRIMARY KEY (log_id, log_user)
--   PARTITION BY RANGE (log_user) (
--   PARTITION p1 VALUES LESS THAN (1),
--   PARTITION p10000 VALUES LESS THAN (10000),
--   PARTITION p20000 VALUES LESS THAN (20000),
--   PARTITION p30000 VALUES LESS THAN (30000),
--   PARTITION p40000 VALUES LESS THAN (40000),
--   PARTITION p50000 VALUES LESS THAN (50000),
--   PARTITION p100000 VALUES LESS THAN (100000),
--   PARTITION p200000 VALUES LESS THAN (200000),
--   PARTITION p300000 VALUES LESS THAN (300000),
--   PARTITION p350000 VALUES LESS THAN (350000),
--   PARTITION p400000 VALUES LESS THAN (400000),
--   PARTITION p500000 VALUES LESS THAN (500000),
--   PARTITION p1000000 VALUES LESS THAN (1000000),
--   PARTITION p2000000 VALUES LESS THAN (2000000),
--   PARTITION p3000000 VALUES LESS THAN (3000000),
--   PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

-- Not needed anymore T239453
-- ALTER TABLE enwiktionary.revision
--   DROP PRIMARY KEY,
--   ADD PRIMARY KEY (rev_id, rev_user),
--   DROP INDEX user_timestamp,
--   ADD INDEX user_timestamp (rev_user, rev_timestamp, rev_id),
--   DROP KEY rev_timestamp,
--   ADD KEY rev_timestamp (rev_timestamp, rev_id),
--   DROP KEY page_timestamp,
--   ADD KEY page_timestamp (rev_page, rev_timestamp, rev_id),
--   DROP KEY usertext_timestamp,
--   ADD KEY usertext_timestamp (rev_user_text, rev_timestamp, rev_id),
--   DROP KEY page_user_timestamp,
--   ADD KEY page_user_timestamp (rev_page, rev_user, rev_timestamp, rev_id),
--   DROP KEY rev_page_id,
--   ADD KEY rev_page_id (rev_page, rev_id)
--   PARTITION BY RANGE (rev_user) (
--   PARTITION p1 VALUES LESS THAN (1),
--   PARTITION p10000 VALUES LESS THAN (10000),
--   PARTITION p20000 VALUES LESS THAN (20000),
--   PARTITION p30000 VALUES LESS THAN (30000),
--   PARTITION p40000 VALUES LESS THAN (40000),
--   PARTITION p50000 VALUES LESS THAN (50000),
--   PARTITION p100000 VALUES LESS THAN (100000),
--   PARTITION p200000 VALUES LESS THAN (200000),
--   PARTITION p300000 VALUES LESS THAN (300000),
--   PARTITION p350000 VALUES LESS THAN (350000),
--   PARTITION p400000 VALUES LESS THAN (400000),
--   PARTITION p500000 VALUES LESS THAN (500000),
--   PARTITION p1000000 VALUES LESS THAN (1000000),
--   PARTITION p2000000 VALUES LESS THAN (2000000),
--   PARTITION p3000000 VALUES LESS THAN (3000000),
--   PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

-- fiwiki

      select       1 as n, count(rev_user) from fiwiki.revision where rev_user  < 1
union select   10000 as n, count(rev_user) from fiwiki.revision where rev_user >= 1      and rev_user < 10000
union select  100000 as n, count(rev_user) from fiwiki.revision where rev_user >= 10000  and rev_user < 100000
union select 1000000 as n, count(rev_user) from fiwiki.revision where rev_user >= 100000 and rev_user < 1000000
union select 2000000 as n, count(rev_user) from fiwiki.revision where rev_user >= 1000000;

-- results on 2017-09-20:
-- +---------+-----------------+
-- | n       | count(rev_user) |
-- +---------+-----------------+
-- |       1 |         2368911 |
-- |   10000 |         3359361 |
-- |  100000 |         6322189 |
-- | 1000000 |         3999004 |
-- | 2000000 |               0 |
-- +---------+-----------------+
-- 5 rows in set (4.22 sec)

-- Not needed anymore T233625
-- ALTER TABLE fiwiki.logging
--   DROP PRIMARY KEY,
--   ADD PRIMARY KEY (log_id, log_user)
--   PARTITION BY RANGE (log_user) (
--   PARTITION p1 VALUES LESS THAN (1),
--   PARTITION p10000 VALUES LESS THAN (10000),
--   PARTITION p50000 VALUES LESS THAN (50000),
--   PARTITION p100000 VALUES LESS THAN (100000),
--   PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

-- Not needed anymore T239453
-- ALTER TABLE fiwiki.revision
--   DROP PRIMARY KEY,
--   ADD PRIMARY KEY (rev_id, rev_user),
--   DROP INDEX user_timestamp,
--   ADD INDEX user_timestamp (rev_user, rev_timestamp, rev_id),
--   DROP KEY rev_timestamp,
--   ADD KEY rev_timestamp (rev_timestamp, rev_id),
--   DROP KEY page_timestamp,
--   ADD KEY page_timestamp (rev_page, rev_timestamp, rev_id),
--   DROP KEY usertext_timestamp,
--   ADD KEY usertext_timestamp (rev_user_text, rev_timestamp, rev_id),
--   DROP KEY page_user_timestamp,
--   ADD KEY page_user_timestamp (rev_page, rev_user, rev_timestamp, rev_id),
--   DROP KEY rev_page_id,
--   ADD KEY rev_page_id (rev_page, rev_id)
--   PARTITION BY RANGE (rev_user) (
--   PARTITION p1 VALUES LESS THAN (1),
--   PARTITION p10000 VALUES LESS THAN (10000),
--   PARTITION p50000 VALUES LESS THAN (50000),
--   PARTITION p100000 VALUES LESS THAN (100000),
--   PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

-- itwiki

      select       1 as n, count(rev_user) from itwiki.revision where rev_user  < 1
union select   10000 as n, count(rev_user) from itwiki.revision where rev_user >= 1       and rev_user <  10000
union select   20000 as n, count(rev_user) from itwiki.revision where rev_user >= 10000   and rev_user <  20000
union select   30000 as n, count(rev_user) from itwiki.revision where rev_user >= 20000   and rev_user <  30000
union select   40000 as n, count(rev_user) from itwiki.revision where rev_user >= 30000   and rev_user <  40000
union select   50000 as n, count(rev_user) from itwiki.revision where rev_user >= 40000   and rev_user <  50000
union select  100000 as n, count(rev_user) from itwiki.revision where rev_user >= 50000   and rev_user < 100000
union select  200000 as n, count(rev_user) from itwiki.revision where rev_user >= 100000  and rev_user < 200000
union select  300000 as n, count(rev_user) from itwiki.revision where rev_user >= 200000  and rev_user < 300000
union select  400000 as n, count(rev_user) from itwiki.revision where rev_user >= 300000  and rev_user < 400000
union select  500000 as n, count(rev_user) from itwiki.revision where rev_user >= 400000  and rev_user < 500000
union select 1000000 as n, count(rev_user) from itwiki.revision where rev_user >= 500000  and rev_user < 1000000
union select 2000000 as n, count(rev_user) from itwiki.revision where rev_user >= 1000000 and rev_user < 2000000
union select 3000000 as n, count(rev_user) from itwiki.revision where rev_user >= 2000000;

-- results on 2017-09-20:
-- +---------+-----------------+
-- | n       | count(rev_user) |
-- +---------+-----------------+
-- |       1 |        15749798 |
-- |   10000 |         5283282 |
-- |   20000 |         1976107 |
-- |   30000 |         1486660 |
-- |   40000 |         2590625 |
-- |   50000 |          900580 |
-- |  100000 |         6711308 |
-- |  200000 |        12213408 |
-- |  300000 |        11082536 |
-- |  400000 |         4574543 |
-- |  500000 |         4481133 |
-- | 1000000 |        14646225 |
-- | 2000000 |         3651405 |
-- | 3000000 |               0 |
-- +---------+-----------------+
-- 14 rows in set (23.51 sec)

-- Not needed anymore T233625
-- ALTER TABLE itwiki.logging
--   DROP PRIMARY KEY,
--   ADD PRIMARY KEY (log_id, log_user)
--   PARTITION BY RANGE (log_user) (
--   PARTITION p1 VALUES LESS THAN (1),
--   PARTITION p10000 VALUES LESS THAN (10000),
--   PARTITION p20000 VALUES LESS THAN (20000),
--   PARTITION p30000 VALUES LESS THAN (30000),
--   PARTITION p40000 VALUES LESS THAN (40000),
--   PARTITION p50000 VALUES LESS THAN (50000),
--   PARTITION p100000 VALUES LESS THAN (100000),
--   PARTITION p150000 VALUES LESS THAN (150000),
--   PARTITION p200000 VALUES LESS THAN (200000),
--   PARTITION p250000 VALUES LESS THAN (250000),
--   PARTITION p300000 VALUES LESS THAN (300000),
--   PARTITION p400000 VALUES LESS THAN (400000),
--   PARTITION p500000 VALUES LESS THAN (500000),
--   PARTITION p600000 VALUES LESS THAN (600000),
--   PARTITION p800000 VALUES LESS THAN (800000),
--   PARTITION p1000000 VALUES LESS THAN (1000000),
--   PARTITION p2000000 VALUES LESS THAN (2000000),
--   PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

-- Not needed anymore T239453
-- ALTER TABLE itwiki.revision
--   DROP PRIMARY KEY,
--   ADD PRIMARY KEY (rev_id, rev_user),
--   DROP INDEX user_timestamp,
--   ADD INDEX user_timestamp (rev_user, rev_timestamp, rev_id),
--   DROP KEY rev_timestamp,
--   ADD KEY rev_timestamp (rev_timestamp, rev_id),
--   DROP KEY page_timestamp,
--   ADD KEY page_timestamp (rev_page, rev_timestamp, rev_id),
--   DROP KEY usertext_timestamp,
--   ADD KEY usertext_timestamp (rev_user_text, rev_timestamp, rev_id),
--   DROP KEY page_user_timestamp,
--   ADD KEY page_user_timestamp (rev_page, rev_user, rev_timestamp, rev_id),
--   DROP KEY rev_page_id,
--   ADD KEY rev_page_id (rev_page, rev_id)
--   PARTITION BY RANGE (rev_user) (
--   PARTITION p1 VALUES LESS THAN (1),
--   PARTITION p10000 VALUES LESS THAN (10000),
--   PARTITION p20000 VALUES LESS THAN (20000),
--   PARTITION p30000 VALUES LESS THAN (30000),
--   PARTITION p40000 VALUES LESS THAN (40000),
--   PARTITION p50000 VALUES LESS THAN (50000),
--   PARTITION p100000 VALUES LESS THAN (100000),
--   PARTITION p150000 VALUES LESS THAN (150000),
--   PARTITION p200000 VALUES LESS THAN (200000),
--   PARTITION p250000 VALUES LESS THAN (250000),
--   PARTITION p300000 VALUES LESS THAN (300000),
--   PARTITION p400000 VALUES LESS THAN (400000),
--   PARTITION p500000 VALUES LESS THAN (500000),
--   PARTITION p600000 VALUES LESS THAN (600000),
--   PARTITION p800000 VALUES LESS THAN (800000),
--   PARTITION p1000000 VALUES LESS THAN (1000000),
--   PARTITION p2000000 VALUES LESS THAN (2000000),
--   PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

-- nlwiki

      select       1 as n, count(rev_user) from nlwiki.revision where rev_user  < 1
union select   10000 as n, count(rev_user) from nlwiki.revision where rev_user >= 1       and rev_user <  10000
union select   20000 as n, count(rev_user) from nlwiki.revision where rev_user >= 10000   and rev_user <  20000
union select   30000 as n, count(rev_user) from nlwiki.revision where rev_user >= 20000   and rev_user <  30000
union select   40000 as n, count(rev_user) from nlwiki.revision where rev_user >= 30000   and rev_user <  40000
union select   50000 as n, count(rev_user) from nlwiki.revision where rev_user >= 40000   and rev_user <  50000
union select  100000 as n, count(rev_user) from nlwiki.revision where rev_user >= 50000   and rev_user < 100000
union select  200000 as n, count(rev_user) from nlwiki.revision where rev_user >= 100000  and rev_user < 200000
union select  300000 as n, count(rev_user) from nlwiki.revision where rev_user >= 200000  and rev_user < 300000
union select  400000 as n, count(rev_user) from nlwiki.revision where rev_user >= 300000  and rev_user < 400000
union select  500000 as n, count(rev_user) from nlwiki.revision where rev_user >= 400000  and rev_user < 500000
union select 1000000 as n, count(rev_user) from nlwiki.revision where rev_user >= 500000  and rev_user < 1000000
union select 2000000 as n, count(rev_user) from nlwiki.revision where rev_user >= 1000000;

-- results on 2017-09-20:
-- +---------+-----------------+
-- | n       | count(rev_user) |
-- +---------+-----------------+
-- |       1 |         4590981 |
-- |   10000 |         6339947 |
-- |   20000 |         3756899 |
-- |   30000 |         1366108 |
-- |   40000 |         1939488 |
-- |   50000 |         1065444 |
-- |  100000 |         5108871 |
-- |  200000 |         7318875 |
-- |  300000 |         5875156 |
-- |  400000 |         3825600 |
-- |  500000 |         2157538 |
-- | 1000000 |         3256761 |
-- | 2000000 |               0 |
-- +---------+-----------------+
-- 13 rows in set (12.30 sec)

-- Not needed anymore T233625
-- ALTER TABLE nlwiki.logging
--   DROP PRIMARY KEY,
--   ADD PRIMARY KEY (log_id, log_user)
--   PARTITION BY RANGE (log_user) (
--   PARTITION p1 VALUES LESS THAN (1),
--   PARTITION p10000 VALUES LESS THAN (10000),
--   PARTITION p20000 VALUES LESS THAN (20000),
--   PARTITION p30000 VALUES LESS THAN (30000),
--   PARTITION p40000 VALUES LESS THAN (40000),
--   PARTITION p50000 VALUES LESS THAN (50000),
--   PARTITION p100000 VALUES LESS THAN (100000),
--   PARTITION p150000 VALUES LESS THAN (150000),
--   PARTITION p200000 VALUES LESS THAN (200000),
--   PARTITION p300000 VALUES LESS THAN (300000),
--   PARTITION p400000 VALUES LESS THAN (400000),
--   PARTITION p500000 VALUES LESS THAN (500000),
--   PARTITION p1000000 VALUES LESS THAN (1000000),
--   PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

-- Not needed anymore T239453
-- ALTER TABLE nlwiki.revision
--   DROP PRIMARY KEY,
--   ADD PRIMARY KEY (rev_id, rev_user),
--   DROP INDEX user_timestamp,
--   ADD INDEX user_timestamp (rev_user, rev_timestamp, rev_id),
--   DROP KEY rev_timestamp,
--   ADD KEY rev_timestamp (rev_timestamp, rev_id),
--   DROP KEY page_timestamp,
--   ADD KEY page_timestamp (rev_page, rev_timestamp, rev_id),
--   DROP KEY usertext_timestamp,
--   ADD KEY usertext_timestamp (rev_user_text, rev_timestamp, rev_id),
--   DROP KEY page_user_timestamp,
--   ADD KEY page_user_timestamp (rev_page, rev_user, rev_timestamp, rev_id),
--   DROP KEY rev_page_id,
--   ADD KEY rev_page_id (rev_page, rev_id)
--   PARTITION BY RANGE (rev_user) (
--   PARTITION p1 VALUES LESS THAN (1),
--   PARTITION p10000 VALUES LESS THAN (10000),
--   PARTITION p20000 VALUES LESS THAN (20000),
--   PARTITION p30000 VALUES LESS THAN (30000),
--   PARTITION p40000 VALUES LESS THAN (40000),
--   PARTITION p50000 VALUES LESS THAN (50000),
--   PARTITION p100000 VALUES LESS THAN (100000),
--   PARTITION p150000 VALUES LESS THAN (150000),
--   PARTITION p200000 VALUES LESS THAN (200000),
--   PARTITION p300000 VALUES LESS THAN (300000),
--   PARTITION p400000 VALUES LESS THAN (400000),
--   PARTITION p500000 VALUES LESS THAN (500000),
--   PARTITION p1000000 VALUES LESS THAN (1000000),
--   PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

-- nowiki

      select       1 as n, count(rev_user) from nowiki.revision where rev_user  < 1
union select   10000 as n, count(rev_user) from nowiki.revision where rev_user >= 1      and rev_user < 10000
union select  100000 as n, count(rev_user) from nowiki.revision where rev_user >= 10000  and rev_user < 100000
union select 1000000 as n, count(rev_user) from nowiki.revision where rev_user >= 100000 and rev_user < 1000000
union select 2000000 as n, count(rev_user) from nowiki.revision where rev_user >= 1000000;

-- results on 2017-09-20:
-- +---------+-----------------+
-- | n       | count(rev_user) |
-- +---------+-----------------+
-- |       1 |         1240561 |
-- |   10000 |         3805119 |
-- |  100000 |         6882907 |
-- | 1000000 |         5119519 |
-- | 2000000 |               0 |
-- +---------+-----------------+
-- 5 rows in set (4.45 sec)


-- Not needed anymore T233625
-- ALTER TABLE nowiki.logging
--   DROP PRIMARY KEY,
--   ADD PRIMARY KEY (log_id, log_user)
--   PARTITION BY RANGE (log_user) (
--   PARTITION p1 VALUES LESS THAN (1),
--   PARTITION p10000 VALUES LESS THAN (10000),
--   PARTITION p100000 VALUES LESS THAN (100000),
--   PARTITION p1000000 VALUES LESS THAN (1000000),
--   PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

-- Not needed anymore T239453
-- ALTER TABLE nowiki.revision
--   DROP PRIMARY KEY,
--   ADD PRIMARY KEY (rev_id, rev_user),
--   DROP INDEX user_timestamp,
--   ADD INDEX user_timestamp (rev_user, rev_timestamp, rev_id),
--   DROP KEY rev_timestamp,
--   ADD KEY rev_timestamp (rev_timestamp, rev_id),
--   DROP KEY page_timestamp,
--   ADD KEY page_timestamp (rev_page, rev_timestamp, rev_id),
--   DROP KEY usertext_timestamp,
--   ADD KEY usertext_timestamp (rev_user_text, rev_timestamp, rev_id),
--   DROP KEY page_user_timestamp,
--   ADD KEY page_user_timestamp (rev_page, rev_user, rev_timestamp, rev_id),
--   DROP KEY rev_page_id,
--   ADD KEY rev_page_id (rev_page, rev_id)
--   PARTITION BY RANGE (rev_user) (
--   PARTITION p1 VALUES LESS THAN (1),
--   PARTITION p10000 VALUES LESS THAN (10000),
--   PARTITION p100000 VALUES LESS THAN (100000),
--   PARTITION p1000000 VALUES LESS THAN (1000000),
--   PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

-- plwiki

      select       1 as n, count(rev_user) from plwiki.revision where rev_user  < 1
union select   10000 as n, count(rev_user) from plwiki.revision where rev_user >= 1       and rev_user <  10000
union select   20000 as n, count(rev_user) from plwiki.revision where rev_user >= 10000   and rev_user <  20000
union select   30000 as n, count(rev_user) from plwiki.revision where rev_user >= 20000   and rev_user <  30000
union select   40000 as n, count(rev_user) from plwiki.revision where rev_user >= 30000   and rev_user <  40000
union select   50000 as n, count(rev_user) from plwiki.revision where rev_user >= 40000   and rev_user <  50000
union select  100000 as n, count(rev_user) from plwiki.revision where rev_user >= 50000   and rev_user < 100000
union select  200000 as n, count(rev_user) from plwiki.revision where rev_user >= 100000  and rev_user < 200000
union select  300000 as n, count(rev_user) from plwiki.revision where rev_user >= 200000  and rev_user < 300000
union select  400000 as n, count(rev_user) from plwiki.revision where rev_user >= 300000  and rev_user < 400000
union select  500000 as n, count(rev_user) from plwiki.revision where rev_user >= 400000  and rev_user < 500000
union select 1000000 as n, count(rev_user) from plwiki.revision where rev_user >= 500000  and rev_user < 1000000
union select 2000000 as n, count(rev_user) from plwiki.revision where rev_user >= 1000000;

-- results on 2017-09-20:
-- +---------+-----------------+
-- | n       | count(rev_user) |
-- +---------+-----------------+
-- |       1 |         5279089 |
-- |   10000 |         3067889 |
-- |   20000 |         2944598 |
-- |   30000 |         1737258 |
-- |   40000 |         3411825 |
-- |   50000 |         1010394 |
-- |  100000 |         5811149 |
-- |  200000 |         7968068 |
-- |  300000 |         4917511 |
-- |  400000 |         3400026 |
-- |  500000 |         2523466 |
-- | 1000000 |         4332452 |
-- | 2000000 |               0 |
-- +---------+-----------------+
-- 13 rows in set (12.56 sec)

-- Not needed anymore T233625
-- ALTER TABLE plwiki.logging
--   DROP PRIMARY KEY,
--   ADD PRIMARY KEY (log_id, log_user)
--   PARTITION BY RANGE (log_user) (
--   PARTITION p1 VALUES LESS THAN (1),
--   PARTITION p10000 VALUES LESS THAN (10000),
--   PARTITION p20000 VALUES LESS THAN (20000),
--   PARTITION p30000 VALUES LESS THAN (30000),
--   PARTITION p40000 VALUES LESS THAN (40000),
--   PARTITION p50000 VALUES LESS THAN (50000),
--   PARTITION p75000 VALUES LESS THAN (75000),
--   PARTITION p100000 VALUES LESS THAN (100000),
--   PARTITION p150000 VALUES LESS THAN (150000),
--   PARTITION p200000 VALUES LESS THAN (200000),
--   PARTITION p300000 VALUES LESS THAN (300000),
--   PARTITION p400000 VALUES LESS THAN (400000),
--   PARTITION p500000 VALUES LESS THAN (500000),
--   PARTITION p1000000 VALUES LESS THAN (1000000),
--   PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

-- Not needed anymore T239453
-- ALTER TABLE plwiki.revision
--   DROP PRIMARY KEY,
--   ADD PRIMARY KEY (rev_id, rev_user),
--   DROP INDEX user_timestamp,
--   ADD INDEX user_timestamp (rev_user, rev_timestamp, rev_id),
--   DROP KEY rev_timestamp,
--   ADD KEY rev_timestamp (rev_timestamp, rev_id),
--   DROP KEY page_timestamp,
--   ADD KEY page_timestamp (rev_page, rev_timestamp, rev_id),
--   DROP KEY usertext_timestamp,
--   ADD KEY usertext_timestamp (rev_user_text, rev_timestamp, rev_id),
--   DROP KEY page_user_timestamp,
--   ADD KEY page_user_timestamp (rev_page, rev_user, rev_timestamp, rev_id),
--   DROP KEY rev_page_id,
--   ADD KEY rev_page_id (rev_page, rev_id)
--   PARTITION BY RANGE (rev_user) (
--   PARTITION p1 VALUES LESS THAN (1),
--   PARTITION p10000 VALUES LESS THAN (10000),
--   PARTITION p20000 VALUES LESS THAN (20000),
--   PARTITION p30000 VALUES LESS THAN (30000),
--   PARTITION p40000 VALUES LESS THAN (40000),
--   PARTITION p50000 VALUES LESS THAN (50000),
--   PARTITION p75000 VALUES LESS THAN (75000),
--   PARTITION p100000 VALUES LESS THAN (100000),
--   PARTITION p150000 VALUES LESS THAN (150000),
--   PARTITION p200000 VALUES LESS THAN (200000),
--   PARTITION p300000 VALUES LESS THAN (300000),
--   PARTITION p400000 VALUES LESS THAN (400000),
--   PARTITION p500000 VALUES LESS THAN (500000),
--   PARTITION p1000000 VALUES LESS THAN (1000000),
--   PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

-- ptwiki

      select       1 as n, count(rev_user) from ptwiki.revision where rev_user  < 1
union select   10000 as n, count(rev_user) from ptwiki.revision where rev_user >= 1       and rev_user <  10000
union select   50000 as n, count(rev_user) from ptwiki.revision where rev_user >= 10000   and rev_user <  50000
union select  100000 as n, count(rev_user) from ptwiki.revision where rev_user >= 50000   and rev_user < 100000
union select  200000 as n, count(rev_user) from ptwiki.revision where rev_user >= 100000  and rev_user < 200000
union select  300000 as n, count(rev_user) from ptwiki.revision where rev_user >= 200000  and rev_user < 300000
union select  400000 as n, count(rev_user) from ptwiki.revision where rev_user >= 300000  and rev_user < 400000
union select  500000 as n, count(rev_user) from ptwiki.revision where rev_user >= 400000  and rev_user < 500000
union select 1000000 as n, count(rev_user) from ptwiki.revision where rev_user >= 500000  and rev_user < 1000000
union select 2000000 as n, count(rev_user) from ptwiki.revision where rev_user >= 1000000 and rev_user < 2000000
union select 3000000 as n, count(rev_user) from ptwiki.revision where rev_user >= 2000000;

-- results on 2017-09-20:
-- +---------+-----------------+
-- | n       | count(rev_user) |
-- +---------+-----------------+
-- |       1 |         9666554 |
-- |   10000 |         2824138 |
-- |   50000 |         2304482 |
-- |  100000 |         3851876 |
-- |  200000 |         3803355 |
-- |  300000 |         2454432 |
-- |  400000 |         2969162 |
-- |  500000 |         3444601 |
-- | 1000000 |        10536151 |
-- | 2000000 |         4075444 |
-- | 3000000 |               0 |
-- +---------+-----------------+
-- 11 rows in set (15.20 sec)

-- Not needed anymore T233625
-- ALTER TABLE ptwiki.logging
--   DROP PRIMARY KEY,
--   ADD PRIMARY KEY (log_id, log_user)
--   PARTITION BY RANGE (log_user) (
--   PARTITION p1 VALUES LESS THAN (1),
--   PARTITION p10000 VALUES LESS THAN (10000),
--   PARTITION p50000 VALUES LESS THAN (50000),
--   PARTITION p100000 VALUES LESS THAN (100000),
--   PARTITION p200000 VALUES LESS THAN (200000),
--   PARTITION p300000 VALUES LESS THAN (300000),
--   PARTITION p400000 VALUES LESS THAN (400000),
--   PARTITION p500000 VALUES LESS THAN (500000),
--   PARTITION p650000 VALUES LESS THAN (650000),
--   PARTITION p800000 VALUES LESS THAN (800000),
--   PARTITION p1000000 VALUES LESS THAN (1000000),
--   PARTITION p2000000 VALUES LESS THAN (2000000),
--   PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

-- Not needed anymore T239453
-- ALTER TABLE ptwiki.revision
--   DROP PRIMARY KEY,
--   ADD PRIMARY KEY (rev_id, rev_user),
--   DROP INDEX user_timestamp,
--   ADD INDEX user_timestamp (rev_user, rev_timestamp, rev_id),
--   DROP KEY rev_timestamp,
--   ADD KEY rev_timestamp (rev_timestamp, rev_id),
--   DROP KEY page_timestamp,
--   ADD KEY page_timestamp (rev_page, rev_timestamp, rev_id),
--   DROP KEY usertext_timestamp,
--   ADD KEY usertext_timestamp (rev_user_text, rev_timestamp, rev_id),
--   DROP KEY page_user_timestamp,
--   ADD KEY page_user_timestamp (rev_page, rev_user, rev_timestamp, rev_id),
--   DROP KEY rev_page_id,
--   ADD KEY rev_page_id (rev_page, rev_id)
--   PARTITION BY RANGE (rev_user) (
--   PARTITION p1 VALUES LESS THAN (1),
--   PARTITION p10000 VALUES LESS THAN (10000),
--   PARTITION p50000 VALUES LESS THAN (50000),
--   PARTITION p100000 VALUES LESS THAN (100000),
--   PARTITION p200000 VALUES LESS THAN (200000),
--   PARTITION p300000 VALUES LESS THAN (300000),
--   PARTITION p400000 VALUES LESS THAN (400000),
--   PARTITION p500000 VALUES LESS THAN (500000),
--   PARTITION p650000 VALUES LESS THAN (650000),
--   PARTITION p800000 VALUES LESS THAN (800000),
--   PARTITION p1000000 VALUES LESS THAN (1000000),
--   PARTITION p2000000 VALUES LESS THAN (2000000),
--   PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

-- svwiki

      select       1 as n, count(rev_user) from svwiki.revision where rev_user  < 1
union select   10000 as n, count(rev_user) from svwiki.revision where rev_user >= 1       and rev_user <   10000
union select   50000 as n, count(rev_user) from svwiki.revision where rev_user >= 10000   and rev_user <   50000
union select  100000 as n, count(rev_user) from svwiki.revision where rev_user >= 50000   and rev_user <  100000
union select  200000 as n, count(rev_user) from svwiki.revision where rev_user >= 100000  and rev_user <  200000
union select  300000 as n, count(rev_user) from svwiki.revision where rev_user >= 200000  and rev_user <  300000
union select 1000000 as n, count(rev_user) from svwiki.revision where rev_user >= 300000  and rev_user < 1000000;

-- results on 2017-09-20:
-- +---------+-----------------+
-- | n       | count(rev_user) |
-- +---------+-----------------+
-- |       1 |         3140147 |
-- |   10000 |         4572613 |
-- |   50000 |         6897591 |
-- |  100000 |         3410662 |
-- |  200000 |         5464678 |
-- |  300000 |        12671727 |
-- | 1000000 |         3587992 |
-- +---------+-----------------+
-- 7 rows in set (9.63 sec)

-- Not needed anymore T233625
-- ALTER TABLE svwiki.logging
--   DROP PRIMARY KEY,
--   ADD PRIMARY KEY (log_id, log_user)
--   PARTITION BY RANGE (log_user) (
--   PARTITION p1 VALUES LESS THAN (1),
--   PARTITION p10000 VALUES LESS THAN (10000),
--   PARTITION p50000 VALUES LESS THAN (50000),
--   PARTITION p100000 VALUES LESS THAN (100000),
--   PARTITION p200000 VALUES LESS THAN (200000),
--   PARTITION p250000 VALUES LESS THAN (250000),
--   PARTITION p300000 VALUES LESS THAN (300000),
--   PARTITION p400000 VALUES LESS THAN (400000),
--   PARTITION p500000 VALUES LESS THAN (500000),
--   PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

-- Not needed anymore T239453
-- ALTER TABLE svwiki.revision
--   DROP PRIMARY KEY,
--   ADD PRIMARY KEY (rev_id, rev_user),
--   DROP INDEX user_timestamp,
--   ADD INDEX user_timestamp (rev_user, rev_timestamp, rev_id),
--   DROP KEY rev_timestamp,
--   ADD KEY rev_timestamp (rev_timestamp, rev_id),
--   DROP KEY page_timestamp,
--   ADD KEY page_timestamp (rev_page, rev_timestamp, rev_id),
--   DROP KEY usertext_timestamp,
--   ADD KEY usertext_timestamp (rev_user_text, rev_timestamp, rev_id),
--   DROP KEY page_user_timestamp,
--   ADD KEY page_user_timestamp (rev_page, rev_user, rev_timestamp, rev_id),
--   DROP KEY rev_page_id,
--   ADD KEY rev_page_id (rev_page, rev_id)
--   PARTITION BY RANGE (rev_user) (
--   PARTITION p1 VALUES LESS THAN (1),
--   PARTITION p10000 VALUES LESS THAN (10000),
--   PARTITION p50000 VALUES LESS THAN (50000),
--   PARTITION p100000 VALUES LESS THAN (100000),
--   PARTITION p200000 VALUES LESS THAN (200000),
--   PARTITION p250000 VALUES LESS THAN (250000),
--   PARTITION p300000 VALUES LESS THAN (300000),
--   PARTITION p400000 VALUES LESS THAN (400000),
--   PARTITION p500000 VALUES LESS THAN (500000),
--   PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

-- thwiki

      select       1 as n, count(rev_user) from thwiki.revision where rev_user  < 1
union select   10000 as n, count(rev_user) from thwiki.revision where rev_user >= 1      and rev_user < 10000
union select  100000 as n, count(rev_user) from thwiki.revision where rev_user >= 10000  and rev_user < 100000
union select 1000000 as n, count(rev_user) from thwiki.revision where rev_user >= 100000 and rev_user < 1000000;

-- results on 2017-09-20:
-- +---------+-----------------+
-- | n       | count(rev_user) |
-- +---------+-----------------+
-- |       1 |         1233683 |
-- |   10000 |         1165227 |
-- |  100000 |         2710044 |
-- | 1000000 |         1513846 |
-- +---------+-----------------+
-- 4 rows in set (2.00 sec)

-- Not needed anymore T233625
-- ALTER TABLE thwiki.logging
--   DROP PRIMARY KEY,
--   ADD PRIMARY KEY (log_id, log_user)
--   PARTITION BY RANGE (log_user) (
--   PARTITION p1 VALUES LESS THAN (1),
--   PARTITION p10000 VALUES LESS THAN (10000),
--   PARTITION p100000 VALUES LESS THAN (100000),
--   PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

-- Not needed anymore T239453
-- ALTER TABLE thwiki.revision
--   DROP PRIMARY KEY,
--   ADD PRIMARY KEY (rev_id, rev_user),
--   DROP INDEX user_timestamp,
--   ADD INDEX user_timestamp (rev_user, rev_timestamp, rev_id),
--   DROP KEY rev_timestamp,
--   ADD KEY rev_timestamp (rev_timestamp, rev_id),
--   DROP KEY page_timestamp,
--   ADD KEY page_timestamp (rev_page, rev_timestamp, rev_id),
--   DROP KEY usertext_timestamp,
--   ADD KEY usertext_timestamp (rev_user_text, rev_timestamp, rev_id),
--   DROP KEY page_user_timestamp,
--   ADD KEY page_user_timestamp (rev_page, rev_user, rev_timestamp, rev_id),
--   DROP KEY rev_page_id,
--   ADD KEY rev_page_id (rev_page, rev_id)
--   PARTITION BY RANGE (rev_user) (
--   PARTITION p1 VALUES LESS THAN (1),
--   PARTITION p10000 VALUES LESS THAN (10000),
--   PARTITION p100000 VALUES LESS THAN (100000),
--   PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

-- trwiki

      select       1 as n, count(rev_user) from trwiki.revision where rev_user  < 1
union select  100000 as n, count(rev_user) from trwiki.revision where rev_user >= 1      and rev_user < 100000
union select  500000 as n, count(rev_user) from trwiki.revision where rev_user >= 100000 and rev_user < 500000
union select 1000000 as n, count(rev_user) from trwiki.revision where rev_user >= 500000 and rev_user < 1000000
union select 2000000 as n, count(rev_user) from trwiki.revision where rev_user >= 1000000;

-- results on 2017-09-20:
-- +---------+-----------------+
-- | n       | count(rev_user) |
-- +---------+-----------------+
-- |       1 |         3356078 |
-- |  100000 |         4477231 |
-- |  500000 |         7546025 |
-- | 1000000 |         1676463 |
-- | 2000000 |               0 |
-- +---------+-----------------+
-- 5 rows in set (7.01 sec)

-- Not needed anymore T233625
-- ALTER TABLE trwiki.logging
--   DROP PRIMARY KEY,
--   ADD PRIMARY KEY (log_id, log_user)
--   PARTITION BY RANGE (log_user) (
--   PARTITION p1 VALUES LESS THAN (1),
--   PARTITION p100000 VALUES LESS THAN (100000),
--   PARTITION p250000 VALUES LESS THAN (250000),
--   PARTITION p500000 VALUES LESS THAN (500000),
--   PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

-- Not needed anymore T239453
-- ALTER TABLE trwiki.revision
--   DROP PRIMARY KEY,
--   ADD PRIMARY KEY (rev_id, rev_user),
--   DROP INDEX user_timestamp,
--   ADD INDEX user_timestamp (rev_user, rev_timestamp, rev_id),
--   DROP KEY rev_timestamp,
--   ADD KEY rev_timestamp (rev_timestamp, rev_id),
--   DROP KEY page_timestamp,
--   ADD KEY page_timestamp (rev_page, rev_timestamp, rev_id),
--   DROP KEY usertext_timestamp,
--   ADD KEY usertext_timestamp (rev_user_text, rev_timestamp, rev_id),
--   DROP KEY page_user_timestamp,
--   ADD KEY page_user_timestamp (rev_page, rev_user, rev_timestamp, rev_id),
--   DROP KEY rev_page_id,
--   ADD KEY rev_page_id (rev_page, rev_id)
--   PARTITION BY RANGE (rev_user) (
--   PARTITION p1 VALUES LESS THAN (1),
--   PARTITION p100000 VALUES LESS THAN (100000),
--   PARTITION p250000 VALUES LESS THAN (250000),
--   PARTITION p500000 VALUES LESS THAN (500000),
--   PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

-- zhwiki

      select       1 as n, count(rev_user) from zhwiki.revision where rev_user  < 1
union select   10000 as n, count(rev_user) from zhwiki.revision where rev_user >= 1       and rev_user <  10000
union select   20000 as n, count(rev_user) from zhwiki.revision where rev_user >= 10000   and rev_user <  20000
union select   50000 as n, count(rev_user) from zhwiki.revision where rev_user >= 20000   and rev_user <  50000
union select  100000 as n, count(rev_user) from zhwiki.revision where rev_user >= 50000   and rev_user < 100000
union select  200000 as n, count(rev_user) from zhwiki.revision where rev_user >= 100000  and rev_user < 200000
union select  300000 as n, count(rev_user) from zhwiki.revision where rev_user >= 200000  and rev_user < 300000
union select  400000 as n, count(rev_user) from zhwiki.revision where rev_user >= 300000  and rev_user < 400000
union select  500000 as n, count(rev_user) from zhwiki.revision where rev_user >= 400000  and rev_user < 500000
union select 1000000 as n, count(rev_user) from zhwiki.revision where rev_user >= 500000  and rev_user < 1000000
union select 2000000 as n, count(rev_user) from zhwiki.revision where rev_user >= 1000000 and rev_user < 2000000
union select 3000000 as n, count(rev_user) from zhwiki.revision where rev_user >= 2000000;

-- results on 2017-09-20:
-- +---------+-----------------+
-- | n       | count(rev_user) |
-- +---------+-----------------+
-- |       1 |         6450168 |
-- |   10000 |         1507870 |
-- |   20000 |         1710563 |
-- |   50000 |         2954974 |
-- |  100000 |         3072475 |
-- |  200000 |         2223542 |
-- |  300000 |         1579237 |
-- |  400000 |         1397183 |
-- |  500000 |         2413770 |
-- | 1000000 |        10602983 |
-- | 2000000 |         7249337 |
-- | 3000000 |         2494584 |
-- +---------+-----------------+
-- 12 rows in set (17.57 sec)

-- Not needed anymore T233625
-- ALTER TABLE zhwiki.logging
--   DROP PRIMARY KEY,
--   ADD PRIMARY KEY (log_id, log_user)
--   PARTITION BY RANGE (log_user) (
--   PARTITION p1 VALUES LESS THAN (1),
--   PARTITION p10000 VALUES LESS THAN (10000),
--   PARTITION p20000 VALUES LESS THAN (20000),
--   PARTITION p50000 VALUES LESS THAN (50000),
--   PARTITION p100000 VALUES LESS THAN (100000),
--   PARTITION p200000 VALUES LESS THAN (200000),
--   PARTITION p300000 VALUES LESS THAN (300000),
--   PARTITION p400000 VALUES LESS THAN (400000),
--   PARTITION p500000 VALUES LESS THAN (500000),
--   PARTITION p750000 VALUES LESS THAN (750000),
--   PARTITION p1000000 VALUES LESS THAN (1000000),
--   PARTITION p1500000 VALUES LESS THAN (1500000),
--   PARTITION p2000000 VALUES LESS THAN (2000000),
--   PARTITION p3000000 VALUES LESS THAN (3000000),
--   PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

-- Not needed anymore T239453
-- ALTER TABLE zhwiki.revision
--   DROP PRIMARY KEY,
--   ADD PRIMARY KEY (rev_id, rev_user),
--   DROP INDEX user_timestamp,
--   ADD INDEX user_timestamp (rev_user, rev_timestamp, rev_id),
--   DROP KEY rev_timestamp,
--   ADD KEY rev_timestamp (rev_timestamp, rev_id),
--   DROP KEY page_timestamp,
--   ADD KEY page_timestamp (rev_page, rev_timestamp, rev_id),
--   DROP KEY usertext_timestamp,
--   ADD KEY usertext_timestamp (rev_user_text, rev_timestamp, rev_id),
--   DROP KEY page_user_timestamp,
--   ADD KEY page_user_timestamp (rev_page, rev_user, rev_timestamp, rev_id),
--   DROP KEY rev_page_id,
--   ADD KEY rev_page_id (rev_page, rev_id)
--   PARTITION BY RANGE (rev_user) (
--   PARTITION p1 VALUES LESS THAN (1),
--   PARTITION p10000 VALUES LESS THAN (10000),
--   PARTITION p20000 VALUES LESS THAN (20000),
--   PARTITION p50000 VALUES LESS THAN (50000),
--   PARTITION p100000 VALUES LESS THAN (100000),
--   PARTITION p200000 VALUES LESS THAN (200000),
--   PARTITION p300000 VALUES LESS THAN (300000),
--   PARTITION p400000 VALUES LESS THAN (400000),
--   PARTITION p500000 VALUES LESS THAN (500000),
--   PARTITION p750000 VALUES LESS THAN (750000),
--   PARTITION p1000000 VALUES LESS THAN (1000000),
--   PARTITION p1500000 VALUES LESS THAN (1500000),
--   PARTITION p2000000 VALUES LESS THAN (2000000),
--   PARTITION p3000000 VALUES LESS THAN (3000000),
--   PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );
