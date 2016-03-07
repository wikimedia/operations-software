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

ALTER TABLE dewiki.logging
  DROP PRIMARY KEY,
  ADD PRIMARY KEY (log_id, log_user)
  PARTITION BY RANGE (log_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p5000 VALUES LESS THAN (5000),
  PARTITION p10000 VALUES LESS THAN (10000),
  PARTITION p20000 VALUES LESS THAN (20000),
  PARTITION p30000 VALUES LESS THAN (30000),
  PARTITION p50000 VALUES LESS THAN (50000),
  PARTITION p70000 VALUES LESS THAN (70000),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION p150000 VALUES LESS THAN (150000),
  PARTITION p200000 VALUES LESS THAN (200000),
  PARTITION p300000 VALUES LESS THAN (300000),
  PARTITION p400000 VALUES LESS THAN (400000),
  PARTITION p500000 VALUES LESS THAN (500000),
  PARTITION p600000 VALUES LESS THAN (600000),
  PARTITION p700000 VALUES LESS THAN (700000),
  PARTITION p800000 VALUES LESS THAN (800000),
  PARTITION p900000 VALUES LESS THAN (900000),
  PARTITION p1000000 VALUES LESS THAN (1000000),
  PARTITION p2000000 VALUES LESS THAN (2000000),
  PARTITION p3000000 VALUES LESS THAN (3000000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

ALTER TABLE dewiki.revision
  DROP PRIMARY KEY,
  DROP INDEX rev_id,
  ADD PRIMARY KEY (rev_id, rev_user)
  PARTITION BY RANGE (rev_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p5000 VALUES LESS THAN (5000),
  PARTITION p10000 VALUES LESS THAN (10000),
  PARTITION p20000 VALUES LESS THAN (20000),
  PARTITION p30000 VALUES LESS THAN (30000),
  PARTITION p50000 VALUES LESS THAN (50000),
  PARTITION p70000 VALUES LESS THAN (70000),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION p150000 VALUES LESS THAN (150000),
  PARTITION p200000 VALUES LESS THAN (200000),
  PARTITION p300000 VALUES LESS THAN (300000),
  PARTITION p400000 VALUES LESS THAN (400000),
  PARTITION p500000 VALUES LESS THAN (500000),
  PARTITION p600000 VALUES LESS THAN (600000),
  PARTITION p700000 VALUES LESS THAN (700000),
  PARTITION p800000 VALUES LESS THAN (800000),
  PARTITION p900000 VALUES LESS THAN (900000),
  PARTITION p1000000 VALUES LESS THAN (1000000),
  PARTITION p2000000 VALUES LESS THAN (2000000),
  PARTITION p3000000 VALUES LESS THAN (3000000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

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

ALTER TABLE wikidatawiki.logging
  DROP PRIMARY KEY,
  ADD PRIMARY KEY (log_id, log_user)
  PARTITION BY RANGE (log_user) (
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

ALTER TABLE wikidatawiki.revision
  DROP PRIMARY KEY,
--  DROP INDEX rev_page_id,
  ADD PRIMARY KEY (rev_id, rev_user)
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

