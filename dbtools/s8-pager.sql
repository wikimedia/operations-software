-- wikidatawiki

      select       1 as n, count(rev_user) from wikidatawiki.revision where rev_user  < 1
union select   10000 as n, count(rev_user) from wikidatawiki.revision where rev_user >= 1       and rev_user < 10000
union select   20000 as n, count(rev_user) from wikidatawiki.revision where rev_user >= 10000   and rev_user < 20000
union select   30000 as n, count(rev_user) from wikidatawiki.revision where rev_user >= 20000   and rev_user < 30000
union select  100000 as n, count(rev_user) from wikidatawiki.revision where rev_user >= 30000   and rev_user < 100000
union select  200000 as n, count(rev_user) from wikidatawiki.revision where rev_user >= 100000  and rev_user < 200000
union select  300000 as n, count(rev_user) from wikidatawiki.revision where rev_user >= 200000  and rev_user < 300000
union select 1000000 as n, count(rev_user) from wikidatawiki.revision where rev_user >= 300000  and rev_user < 1000000
union select 2000000 as n, count(rev_user) from wikidatawiki.revision where rev_user >= 1000000 and rev_user < 2000000
union select 3000000 as n, count(rev_user) from wikidatawiki.revision where rev_user >= 2000000;

-- results on 2016-03-07:
-- +---------+-----------------+
-- | n       | count(rev_user) |
-- +---------+-----------------+
-- |       1 |         1467305 |
-- |   10000 |        28725758 |
-- |   20000 |        21309827 |
-- |   30000 |        27248967 |
-- |  100000 |        40315544 |
-- |  200000 |        71837026 |
-- |  300000 |        26518572 |
-- | 1000000 |        54299316 |
-- | 2000000 |        33821553 |
-- | 3000000 |         2507345 |
-- +---------+-----------------+
-- 10 rows in set (22 min 54.92 sec)

-- Not needed anymore T233625
-- ALTER TABLE wikidatawiki.logging
--   DROP PRIMARY KEY,
--   ADD PRIMARY KEY (log_id, log_user)
--   PARTITION BY RANGE (log_user) (
--   PARTITION p1 VALUES LESS THAN (1),
--   PARTITION p5000 VALUES LESS THAN (5000),
--   PARTITION p10000 VALUES LESS THAN (10000),
--   PARTITION p15000 VALUES LESS THAN (15000),
--   PARTITION p20000 VALUES LESS THAN (20000),
--   PARTITION p25000 VALUES LESS THAN (25000),
--   PARTITION p30000 VALUES LESS THAN (30000),
--   PARTITION p50000 VALUES LESS THAN (50000),
--   PARTITION p70000 VALUES LESS THAN (70000),
--   PARTITION p100000 VALUES LESS THAN (100000),
--   PARTITION p125000 VALUES LESS THAN (125000),
--   PARTITION p150000 VALUES LESS THAN (150000),
--   PARTITION p175000 VALUES LESS THAN (175000),
--   PARTITION p200000 VALUES LESS THAN (200000),
--   PARTITION p250000 VALUES LESS THAN (250000),
--   PARTITION p300000 VALUES LESS THAN (300000),
--   PARTITION p500000 VALUES LESS THAN (500000),
--   PARTITION p700000 VALUES LESS THAN (700000),
--   PARTITION p1000000 VALUES LESS THAN (1000000),
--   PARTITION p1500000 VALUES LESS THAN (1500000),
--   PARTITION p2000000 VALUES LESS THAN (2000000),
--   PARTITION p3000000 VALUES LESS THAN (3000000),
--   PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

ALTER TABLE wikidatawiki.revision
  DROP PRIMARY KEY,
  ADD PRIMARY KEY (rev_id, rev_user),
  DROP INDEX user_timestamp,
  ADD INDEX user_timestamp (rev_user, rev_timestamp, rev_id),
  DROP KEY rev_timestamp,
  ADD KEY rev_timestamp (rev_timestamp, rev_id),
  DROP KEY page_timestamp,
  ADD KEY page_timestamp (rev_page, rev_timestamp, rev_id),
  DROP KEY usertext_timestamp,
  ADD KEY usertext_timestamp (rev_user_text, rev_timestamp, rev_id),
  DROP KEY page_user_timestamp,
  ADD KEY page_user_timestamp (rev_page, rev_user, rev_timestamp, rev_id),
  DROP KEY rev_page_id,
  ADD KEY rev_page_id (rev_page, rev_id)
  PARTITION BY RANGE (rev_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p5000 VALUES LESS THAN (5000),
  PARTITION p10000 VALUES LESS THAN (10000),
  PARTITION p15000 VALUES LESS THAN (15000),
  PARTITION p20000 VALUES LESS THAN (20000),
  PARTITION p25000 VALUES LESS THAN (25000),
  PARTITION p30000 VALUES LESS THAN (30000),
  PARTITION p50000 VALUES LESS THAN (50000),
  PARTITION p70000 VALUES LESS THAN (70000),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION p125000 VALUES LESS THAN (125000),
  PARTITION p150000 VALUES LESS THAN (150000),
  PARTITION p175000 VALUES LESS THAN (175000),
  PARTITION p200000 VALUES LESS THAN (200000),
  PARTITION p250000 VALUES LESS THAN (250000),
  PARTITION p300000 VALUES LESS THAN (300000),
  PARTITION p500000 VALUES LESS THAN (500000),
  PARTITION p700000 VALUES LESS THAN (700000),
  PARTITION p1000000 VALUES LESS THAN (1000000),
  PARTITION p1500000 VALUES LESS THAN (1500000),
  PARTITION p2000000 VALUES LESS THAN (2000000),
  PARTITION p3000000 VALUES LESS THAN (3000000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

