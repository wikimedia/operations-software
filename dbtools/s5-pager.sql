-- dewiki

      select       1 as n, count(rev_user) from dewiki.revision where rev_user  < 1
union select   10000 as n, count(rev_user) from dewiki.revision where rev_user >= 1       and rev_user < 10000
union select   20000 as n, count(rev_user) from dewiki.revision where rev_user >= 10000   and rev_user < 20000
union select   30000 as n, count(rev_user) from dewiki.revision where rev_user >= 20000   and rev_user < 30000
union select  100000 as n, count(rev_user) from dewiki.revision where rev_user >= 30000   and rev_user < 100000
union select  200000 as n, count(rev_user) from dewiki.revision where rev_user >= 100000  and rev_user < 200000
union select  300000 as n, count(rev_user) from dewiki.revision where rev_user >= 200000  and rev_user < 300000
union select 1000000 as n, count(rev_user) from dewiki.revision where rev_user >= 300000  and rev_user < 1000000
union select 2000000 as n, count(rev_user) from dewiki.revision where rev_user >= 1000000 and rev_user < 2000000
union select 3000000 as n, count(rev_user) from dewiki.revision where rev_user >= 2000000;

-- results on 2016-03-07:
-- +---------+-----------------+
-- | n       | count(rev_user) |
-- +---------+-----------------+
-- |       1 |        23175897 |
-- |   10000 |         6689692 |
-- |   20000 |         3446708 |
-- |   30000 |         3900499 |
-- |  100000 |        18133533 |
-- |  200000 |        14848243 |
-- |  300000 |        14203410 |
-- | 1000000 |        40046991 |
-- | 2000000 |        13909989 |
-- | 3000000 |         1204622 |
-- +---------+-----------------+
-- 10 rows in set (12 min 19.38 sec)

-- Not needed anymore T233625
-- ALTER TABLE dewiki.logging
--   DROP PRIMARY KEY,
--   ADD PRIMARY KEY (log_id, log_user)
--   PARTITION BY RANGE (log_user) (
--   PARTITION p1 VALUES LESS THAN (1),
--   PARTITION p5000 VALUES LESS THAN (5000),
--   PARTITION p10000 VALUES LESS THAN (10000),
--   PARTITION p20000 VALUES LESS THAN (20000),
--   PARTITION p30000 VALUES LESS THAN (30000),
--   PARTITION p50000 VALUES LESS THAN (50000),
--   PARTITION p70000 VALUES LESS THAN (70000),
--   PARTITION p100000 VALUES LESS THAN (100000),
--   PARTITION p150000 VALUES LESS THAN (150000),
--   PARTITION p200000 VALUES LESS THAN (200000),
--   PARTITION p300000 VALUES LESS THAN (300000),
--   PARTITION p400000 VALUES LESS THAN (400000),
--   PARTITION p500000 VALUES LESS THAN (500000),
--   PARTITION p600000 VALUES LESS THAN (600000),
--   PARTITION p700000 VALUES LESS THAN (700000),
--   PARTITION p800000 VALUES LESS THAN (800000),
--   PARTITION p900000 VALUES LESS THAN (900000),
--   PARTITION p1000000 VALUES LESS THAN (1000000),
--   PARTITION p2000000 VALUES LESS THAN (2000000),
--   PARTITION p3000000 VALUES LESS THAN (3000000),
--   PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

-- Not neeed anymore T239453
-- ALTER TABLE dewiki.revision
-- DROP PRIMARY KEY,
-- ADD PRIMARY KEY (rev_id, rev_user),
-- DROP INDEX user_timestamp,
-- ADD INDEX user_timestamp (rev_user, rev_timestamp, rev_id),
-- DROP KEY rev_timestamp,
-- ADD KEY rev_timestamp (rev_timestamp, rev_id),
-- DROP KEY page_timestamp,
-- ADD KEY page_timestamp (rev_page, rev_timestamp, rev_id),
-- DROP KEY usertext_timestamp,
-- ADD KEY usertext_timestamp (rev_user_text, rev_timestamp, rev_id),
-- DROP KEY page_user_timestamp,
-- ADD KEY page_user_timestamp (rev_page, rev_user, rev_timestamp, rev_id),
-- DROP KEY rev_page_id,
-- ADD KEY rev_page_id (rev_page, rev_id)
-- PARTITION BY RANGE (rev_user) (
-- PARTITION p1 VALUES LESS THAN (1),
-- PARTITION p5000 VALUES LESS THAN (5000),
-- PARTITION p10000 VALUES LESS THAN (10000),
-- PARTITION p20000 VALUES LESS THAN (20000),
-- PARTITION p30000 VALUES LESS THAN (30000),
-- PARTITION p50000 VALUES LESS THAN (50000),
-- PARTITION p70000 VALUES LESS THAN (70000),
-- PARTITION p100000 VALUES LESS THAN (100000),
-- PARTITION p150000 VALUES LESS THAN (150000),
-- PARTITION p200000 VALUES LESS THAN (200000),
-- PARTITION p300000 VALUES LESS THAN (300000),
-- PARTITION p400000 VALUES LESS THAN (400000),
-- PARTITION p500000 VALUES LESS THAN (500000),
-- PARTITION p600000 VALUES LESS THAN (600000),
-- PARTITION p700000 VALUES LESS THAN (700000),
-- PARTITION p800000 VALUES LESS THAN (800000),
-- PARTITION p900000 VALUES LESS THAN (900000),
-- PARTITION p1000000 VALUES LESS THAN (1000000),
-- PARTITION p2000000 VALUES LESS THAN (2000000),
-- PARTITION p3000000 VALUES LESS THAN (3000000),
-- PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );
