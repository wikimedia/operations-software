-- bgwiki

      select       1 as n, count(rev_user) from bgwiki.revision where rev_user  < 1
union select   10000 as n, count(rev_user) from bgwiki.revision where rev_user >= 1      and rev_user < 10000
union select  100000 as n, count(rev_user) from bgwiki.revision where rev_user >= 10000  and rev_user < 100000
union select 1000000 as n, count(rev_user) from bgwiki.revision where rev_user >= 100000 and rev_user < 1000000
union select 2000000 as n, count(rev_user) from bgwiki.revision where rev_user >= 1000000;

-- results on 2016-03-08:
-- +---------+-----------------+
-- | n       | count(rev_user) |
-- +---------+-----------------+
-- |       1 |          903947 |
-- |   10000 |         2148330 |
-- |  100000 |         3003957 |
-- | 1000000 |          772584 |
-- | 2000000 |               0 |
-- +---------+-----------------+
-- 5 rows in set (1.73 sec)

ALTER TABLE bgwiki.logging
  DROP PRIMARY KEY,
  ADD PRIMARY KEY (log_id, log_user)
  PARTITION BY RANGE (log_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p10000 VALUES LESS THAN (10000),
  PARTITION p50000 VALUES LESS THAN (50000),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

ALTER TABLE bgwiki.revision
  DROP PRIMARY KEY,
  DROP INDEX rev_id,
  ADD PRIMARY KEY (rev_id, rev_user)
  PARTITION BY RANGE (rev_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p10000 VALUES LESS THAN (10000),
  PARTITION p50000 VALUES LESS THAN (50000),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

-- cswiki

      select       1 as n, count(rev_user) from cswiki.revision where rev_user  < 1
union select   10000 as n, count(rev_user) from cswiki.revision where rev_user >= 1      and rev_user < 10000
union select  100000 as n, count(rev_user) from cswiki.revision where rev_user >= 10000  and rev_user < 100000
union select 1000000 as n, count(rev_user) from cswiki.revision where rev_user >= 100000 and rev_user < 1000000
union select 2000000 as n, count(rev_user) from cswiki.revision where rev_user >= 1000000;

-- results on 2016-03-08:
-- +---------+-----------------+
-- | n       | count(rev_user) |
-- +---------+-----------------+
-- |       1 |         1225371 |
-- |   10000 |         3870115 |
-- |  100000 |         4904869 |
-- | 1000000 |         2676888 |
-- | 2000000 |               0 |
-- +---------+-----------------+
-- 5 rows in set (2 min 14.52 sec)

ALTER TABLE cswiki.logging
  DROP PRIMARY KEY,
  ADD PRIMARY KEY (log_id, log_user)
  PARTITION BY RANGE (log_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p10000 VALUES LESS THAN (10000),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

ALTER TABLE cswiki.revision
  DROP PRIMARY KEY,
  DROP INDEX rev_id,
  ADD PRIMARY KEY (rev_id, rev_user)
  PARTITION BY RANGE (rev_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p10000 VALUES LESS THAN (10000),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

-- enwikiquote

      select       1 as n, count(rev_user) from enwikiquote.revision where rev_user  < 1
union select   10000 as n, count(rev_user) from enwikiquote.revision where rev_user >= 1      and rev_user < 10000
union select  100000 as n, count(rev_user) from enwikiquote.revision where rev_user >= 10000  and rev_user < 100000
union select 1000000 as n, count(rev_user) from enwikiquote.revision where rev_user >= 100000 and rev_user < 1000000
union select 2000000 as n, count(rev_user) from enwikiquote.revision where rev_user >= 1000000;

-- results on 2016-03-08:
-- +---------+-----------------+
-- | n       | count(rev_user) |
-- +---------+-----------------+
-- |       1 |          766967 |
-- |   10000 |          453557 |
-- |  100000 |          330448 |
-- | 1000000 |          279150 |
-- | 2000000 |           97901 |
-- +---------+-----------------+
-- 5 rows in set (1 min 14.91 sec)

ALTER TABLE enwikiquote.logging
  DROP PRIMARY KEY,
  ADD PRIMARY KEY (log_id, log_user)
  PARTITION BY RANGE (log_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p10000 VALUES LESS THAN (10000),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

ALTER TABLE enwikiquote.revision
  DROP PRIMARY KEY,
  DROP INDEX rev_id,
  ADD PRIMARY KEY (rev_id, rev_user)
  PARTITION BY RANGE (rev_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p10000 VALUES LESS THAN (10000),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

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

-- results on 2016-03-08:
-- +---------+-----------------+
-- | n       | count(rev_user) |
-- +---------+-----------------+
-- |       1 |         1088949 |
-- |   10000 |         3506698 |
-- |   20000 |          947482 |
-- |   30000 |         1419086 |
-- |   40000 |         2439779 |
-- |   50000 |         6499965 |
-- |  100000 |         2351610 |
-- |  200000 |          447897 |
-- |  300000 |         4029361 |
-- |  400000 |         9274848 |
-- |  500000 |         1349585 |
-- | 1000000 |         1043189 |
-- | 2000000 |         1047336 |
-- | 3000000 |           11288 |
-- +---------+-----------------+
-- 14 rows in set (1 min 6.99 sec)

ALTER TABLE enwiktionary.logging
  DROP PRIMARY KEY,
  ADD PRIMARY KEY (log_id, log_user)
  PARTITION BY RANGE (log_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p10000 VALUES LESS THAN (10000),
  PARTITION p20000 VALUES LESS THAN (20000),
  PARTITION p30000 VALUES LESS THAN (30000),
  PARTITION p40000 VALUES LESS THAN (40000),
  PARTITION p50000 VALUES LESS THAN (50000),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION p200000 VALUES LESS THAN (200000),
  PARTITION p300000 VALUES LESS THAN (300000),
  PARTITION p350000 VALUES LESS THAN (350000),
  PARTITION p400000 VALUES LESS THAN (400000),
  PARTITION p500000 VALUES LESS THAN (500000),
  PARTITION p1000000 VALUES LESS THAN (1000000),
  PARTITION p2000000 VALUES LESS THAN (2000000),
  PARTITION p3000000 VALUES LESS THAN (3000000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

ALTER TABLE enwiktionary.revision
  DROP PRIMARY KEY,
  DROP INDEX rev_id,
  ADD PRIMARY KEY (rev_id, rev_user)
  PARTITION BY RANGE (rev_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p10000 VALUES LESS THAN (10000),
  PARTITION p20000 VALUES LESS THAN (20000),
  PARTITION p30000 VALUES LESS THAN (30000),
  PARTITION p40000 VALUES LESS THAN (40000),
  PARTITION p50000 VALUES LESS THAN (50000),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION p200000 VALUES LESS THAN (200000),
  PARTITION p300000 VALUES LESS THAN (300000),
  PARTITION p350000 VALUES LESS THAN (350000),
  PARTITION p400000 VALUES LESS THAN (400000),
  PARTITION p500000 VALUES LESS THAN (500000),
  PARTITION p1000000 VALUES LESS THAN (1000000),
  PARTITION p2000000 VALUES LESS THAN (2000000),
  PARTITION p3000000 VALUES LESS THAN (3000000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

-- fiwiki

      select       1 as n, count(rev_user) from fiwiki.revision where rev_user  < 1
union select   10000 as n, count(rev_user) from fiwiki.revision where rev_user >= 1      and rev_user < 10000
union select  100000 as n, count(rev_user) from fiwiki.revision where rev_user >= 10000  and rev_user < 100000
union select 1000000 as n, count(rev_user) from fiwiki.revision where rev_user >= 100000 and rev_user < 1000000
union select 2000000 as n, count(rev_user) from fiwiki.revision where rev_user >= 1000000;

-- results on 2016-03-08:
-- +---------+-----------------+
-- | n       | count(rev_user) |
-- +---------+-----------------+
-- |       1 |         2185285 |
-- |   10000 |         3214324 |
-- |  100000 |         6062824 |
-- | 1000000 |         3424978 |
-- | 2000000 |               0 |
-- +---------+-----------------+
5 rows in set (27.11 sec)

ALTER TABLE fiwiki.logging
  DROP PRIMARY KEY,
  ADD PRIMARY KEY (log_id, log_user)
  PARTITION BY RANGE (log_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p10000 VALUES LESS THAN (10000),
  PARTITION p50000 VALUES LESS THAN (50000),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

ALTER TABLE fiwiki.revision
  DROP PRIMARY KEY,
  DROP INDEX rev_id,
  ADD PRIMARY KEY (rev_id, rev_user)
  PARTITION BY RANGE (rev_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p10000 VALUES LESS THAN (10000),
  PARTITION p50000 VALUES LESS THAN (50000),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

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

-- results on 2016-03-08:
-- +---------+-----------------+
-- | n       | count(rev_user) |
-- +---------+-----------------+
-- |       1 |        13603340 |
-- |   10000 |         4818558 |
-- |   20000 |         1938854 |
-- |   30000 |         1438740 |
-- |   40000 |         2431179 |
-- |   50000 |          856054 |
-- |  100000 |         6369713 |
-- |  200000 |        11119159 |
-- |  300000 |        10053293 |
-- |  400000 |         4235306 |
-- |  500000 |         4172320 |
-- | 1000000 |        11788989 |
-- | 2000000 |          984619 |
-- | 3000000 |               0 |
-- +---------+-----------------+
-- 14 rows in set (2 min 37.98 sec)

ALTER TABLE itwiki.logging
  DROP PRIMARY KEY,
  ADD PRIMARY KEY (log_id, log_user)
  PARTITION BY RANGE (log_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p10000 VALUES LESS THAN (10000),
  PARTITION p20000 VALUES LESS THAN (20000),
  PARTITION p30000 VALUES LESS THAN (30000),
  PARTITION p40000 VALUES LESS THAN (40000),
  PARTITION p50000 VALUES LESS THAN (50000),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION p150000 VALUES LESS THAN (150000),
  PARTITION p200000 VALUES LESS THAN (200000),
  PARTITION p250000 VALUES LESS THAN (250000),
  PARTITION p300000 VALUES LESS THAN (300000),
  PARTITION p400000 VALUES LESS THAN (400000),
  PARTITION p500000 VALUES LESS THAN (500000),
  PARTITION p750000 VALUES LESS THAN (750000),
  PARTITION p1000000 VALUES LESS THAN (1000000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

ALTER TABLE itwiki.revision
  DROP PRIMARY KEY,
  DROP INDEX rev_id,
  ADD PRIMARY KEY (rev_id, rev_user)
  PARTITION BY RANGE (rev_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p10000 VALUES LESS THAN (10000),
  PARTITION p20000 VALUES LESS THAN (20000),
  PARTITION p30000 VALUES LESS THAN (30000),
  PARTITION p40000 VALUES LESS THAN (40000),
  PARTITION p50000 VALUES LESS THAN (50000),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION p150000 VALUES LESS THAN (150000),
  PARTITION p200000 VALUES LESS THAN (200000),
  PARTITION p250000 VALUES LESS THAN (250000),
  PARTITION p300000 VALUES LESS THAN (300000),
  PARTITION p400000 VALUES LESS THAN (400000),
  PARTITION p500000 VALUES LESS THAN (500000),
  PARTITION p750000 VALUES LESS THAN (750000),
  PARTITION p1000000 VALUES LESS THAN (1000000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

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

-- results on 2016-03-08:
-- +---------+-----------------+
-- | n       | count(rev_user) |
-- +---------+-----------------+
-- |       1 |         4163116 |
-- |   10000 |         6144952 |
-- |   20000 |         3612280 |
-- |   30000 |         1362992 |
-- |   40000 |         1882182 |
-- |   50000 |          990176 |
-- |  100000 |         4834840 |
-- |  200000 |         6958755 |
-- |  300000 |         5594085 |
-- |  400000 |         3566284 |
-- |  500000 |         1868596 |
-- | 1000000 |         2343797 |
-- | 2000000 |               0 |
-- +---------+-----------------+

ALTER TABLE nlwiki.logging
  DROP PRIMARY KEY,
  ADD PRIMARY KEY (log_id, log_user)
  PARTITION BY RANGE (log_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p10000 VALUES LESS THAN (10000),
  PARTITION p20000 VALUES LESS THAN (20000),
  PARTITION p30000 VALUES LESS THAN (30000),
  PARTITION p40000 VALUES LESS THAN (40000),
  PARTITION p50000 VALUES LESS THAN (50000),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION p150000 VALUES LESS THAN (150000),
  PARTITION p200000 VALUES LESS THAN (200000),
  PARTITION p300000 VALUES LESS THAN (300000),
  PARTITION p400000 VALUES LESS THAN (400000),
  PARTITION p500000 VALUES LESS THAN (500000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

ALTER TABLE nlwiki.revision
  DROP PRIMARY KEY,
  DROP INDEX rev_id,
  ADD PRIMARY KEY (rev_id, rev_user)
  PARTITION BY RANGE (rev_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p10000 VALUES LESS THAN (10000),
  PARTITION p20000 VALUES LESS THAN (20000),
  PARTITION p30000 VALUES LESS THAN (30000),
  PARTITION p40000 VALUES LESS THAN (40000),
  PARTITION p50000 VALUES LESS THAN (50000),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION p150000 VALUES LESS THAN (150000),
  PARTITION p200000 VALUES LESS THAN (200000),
  PARTITION p300000 VALUES LESS THAN (300000),
  PARTITION p400000 VALUES LESS THAN (400000),
  PARTITION p500000 VALUES LESS THAN (500000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

-- nowiki

      select       1 as n, count(rev_user) from nowiki.revision where rev_user  < 1
union select   10000 as n, count(rev_user) from nowiki.revision where rev_user >= 1      and rev_user < 10000
union select  100000 as n, count(rev_user) from nowiki.revision where rev_user >= 10000  and rev_user < 100000
union select 1000000 as n, count(rev_user) from nowiki.revision where rev_user >= 100000 and rev_user < 1000000
union select 2000000 as n, count(rev_user) from nowiki.revision where rev_user >= 1000000;

-- results on 2016-03-08:
-- +---------+-----------------+
-- | n       | count(rev_user) |
-- +---------+-----------------+
-- |       1 |         1119949 |
-- |   10000 |         3596329 |
-- |  100000 |         6077737 |
-- | 1000000 |         4365985 |
-- +---------+-----------------+
-- 4 rows in set (42.18 sec)

ALTER TABLE nowiki.logging
  DROP PRIMARY KEY,
  ADD PRIMARY KEY (log_id, log_user)
  PARTITION BY RANGE (log_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p10000 VALUES LESS THAN (10000),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

ALTER TABLE nowiki.revision
  DROP PRIMARY KEY,
  DROP INDEX rev_id,
  ADD PRIMARY KEY (rev_id, rev_user)
  PARTITION BY RANGE (rev_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p10000 VALUES LESS THAN (10000),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

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

-- results on 2016-03-08:
-- +---------+-----------------+
-- | n       | count(rev_user) |
-- +---------+-----------------+
-- |       1 |         4900476 |
-- |   10000 |         2996143 |
-- |   20000 |         2817380 |
-- |   30000 |         1657955 |
-- |   40000 |         3079880 |
-- |   50000 |          996358 |
-- |  100000 |         5508649 |
-- |  200000 |         7160471 |
-- |  300000 |         4558427 |
-- |  400000 |         3110678 |
-- |  500000 |         2170635 |
-- | 1000000 |         2750341 |
-- | 2000000 |               0 |
-- +---------+-----------------+
-- 13 rows in set (1 min 43.65 sec)

ALTER TABLE plwiki.logging
  DROP PRIMARY KEY,
  ADD PRIMARY KEY (log_id, log_user)
  PARTITION BY RANGE (log_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p10000 VALUES LESS THAN (10000),
  PARTITION p20000 VALUES LESS THAN (20000),
  PARTITION p30000 VALUES LESS THAN (30000),
  PARTITION p40000 VALUES LESS THAN (40000),
  PARTITION p50000 VALUES LESS THAN (50000),
  PARTITION p75000 VALUES LESS THAN (75000),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION p150000 VALUES LESS THAN (150000),
  PARTITION p200000 VALUES LESS THAN (200000),
  PARTITION p300000 VALUES LESS THAN (300000),
  PARTITION p400000 VALUES LESS THAN (400000),
  PARTITION p500000 VALUES LESS THAN (500000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

ALTER TABLE plwiki.revision
  DROP PRIMARY KEY,
  DROP INDEX rev_id,
  ADD PRIMARY KEY (rev_id, rev_user)
  PARTITION BY RANGE (rev_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p10000 VALUES LESS THAN (10000),
  PARTITION p20000 VALUES LESS THAN (20000),
  PARTITION p30000 VALUES LESS THAN (30000),
  PARTITION p40000 VALUES LESS THAN (40000),
  PARTITION p50000 VALUES LESS THAN (50000),
  PARTITION p75000 VALUES LESS THAN (75000),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION p150000 VALUES LESS THAN (150000),
  PARTITION p200000 VALUES LESS THAN (200000),
  PARTITION p300000 VALUES LESS THAN (300000),
  PARTITION p400000 VALUES LESS THAN (400000),
  PARTITION p500000 VALUES LESS THAN (500000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

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

-- results on 2016-03-08:
-- +---------+-----------------+
-- | n       | count(rev_user) |
-- +---------+-----------------+
-- |       1 |         8485522 |
-- |   10000 |         2782285 |
-- |   50000 |         2264550 |
-- |  100000 |         3648770 |
-- |  200000 |         3645097 |
-- |  300000 |         2299734 |
-- |  400000 |         2815469 |
-- |  500000 |         3177825 |
-- | 1000000 |         9708497 |
-- | 2000000 |         2629705 |
-- | 3000000 |               0 |
-- +---------+-----------------+
-- 11 rows in set (1 min 28.19 sec)

ALTER TABLE ptwiki.logging
  DROP PRIMARY KEY,
  ADD PRIMARY KEY (log_id, log_user)
  PARTITION BY RANGE (log_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p10000 VALUES LESS THAN (10000),
  PARTITION p50000 VALUES LESS THAN (50000),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION p200000 VALUES LESS THAN (200000),
  PARTITION p300000 VALUES LESS THAN (300000),
  PARTITION p400000 VALUES LESS THAN (400000),
  PARTITION p500000 VALUES LESS THAN (500000),
  PARTITION p650000 VALUES LESS THAN (650000),
  PARTITION p800000 VALUES LESS THAN (800000),
  PARTITION p1000000 VALUES LESS THAN (1000000),
  PARTITION p2000000 VALUES LESS THAN (2000000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

ALTER TABLE ptwiki.revision
  DROP PRIMARY KEY,
  DROP INDEX rev_id,
  ADD PRIMARY KEY (rev_id, rev_user)
  PARTITION BY RANGE (rev_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p10000 VALUES LESS THAN (10000),
  PARTITION p50000 VALUES LESS THAN (50000),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION p200000 VALUES LESS THAN (200000),
  PARTITION p300000 VALUES LESS THAN (300000),
  PARTITION p400000 VALUES LESS THAN (400000),
  PARTITION p500000 VALUES LESS THAN (500000),
  PARTITION p650000 VALUES LESS THAN (650000),
  PARTITION p800000 VALUES LESS THAN (800000),
  PARTITION p1000000 VALUES LESS THAN (1000000),
  PARTITION p2000000 VALUES LESS THAN (2000000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

-- svwiki

      select       1 as n, count(rev_user) from svwiki.revision where rev_user  < 1
union select   10000 as n, count(rev_user) from svwiki.revision where rev_user >= 1       and rev_user <   10000
union select   50000 as n, count(rev_user) from svwiki.revision where rev_user >= 10000   and rev_user <   50000
union select  100000 as n, count(rev_user) from svwiki.revision where rev_user >= 50000   and rev_user <  100000
union select  200000 as n, count(rev_user) from svwiki.revision where rev_user >= 100000  and rev_user <  200000
union select  300000 as n, count(rev_user) from svwiki.revision where rev_user >= 200000  and rev_user <  300000
union select 1000000 as n, count(rev_user) from svwiki.revision where rev_user >= 300000  and rev_user < 1000000;

-- results on 2016-03-08:
-- +---------+-----------------+
-- | n       | count(rev_user) |
-- +---------+-----------------+
-- |       1 |         2907677 |
-- |   10000 |         4426063 |
-- |   50000 |         6434996 |
-- |  100000 |         2791745 |
-- |  200000 |         4279150 |
-- |  300000 |         9667527 |
-- | 1000000 |         1951754 |
-- +---------+-----------------+
-- 7 rows in set (1 min 0.30 sec)

ALTER TABLE svwiki.logging
  DROP PRIMARY KEY,
  ADD PRIMARY KEY (log_id, log_user)
  PARTITION BY RANGE (log_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p10000 VALUES LESS THAN (10000),
  PARTITION p50000 VALUES LESS THAN (50000),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION p200000 VALUES LESS THAN (200000),
  PARTITION p250000 VALUES LESS THAN (250000),
  PARTITION p300000 VALUES LESS THAN (300000),
  PARTITION p400000 VALUES LESS THAN (400000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

ALTER TABLE svwiki.revision
  DROP PRIMARY KEY,
  DROP INDEX rev_id,
  ADD PRIMARY KEY (rev_id, rev_user)
  PARTITION BY RANGE (rev_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p10000 VALUES LESS THAN (10000),
  PARTITION p50000 VALUES LESS THAN (50000),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION p200000 VALUES LESS THAN (200000),
  PARTITION p250000 VALUES LESS THAN (250000),
  PARTITION p300000 VALUES LESS THAN (300000),
  PARTITION p400000 VALUES LESS THAN (400000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

-- thwiki

      select       1 as n, count(rev_user) from thwiki.revision where rev_user  < 1
union select   10000 as n, count(rev_user) from thwiki.revision where rev_user >= 1      and rev_user < 10000
union select  100000 as n, count(rev_user) from thwiki.revision where rev_user >= 10000  and rev_user < 100000
union select 1000000 as n, count(rev_user) from thwiki.revision where rev_user >= 100000 and rev_user < 1000000;

-- results on 2016-03-08:
-- +---------+-----------------+
-- | n       | count(rev_user) |
-- +---------+-----------------+
-- |       1 |          987804 |
-- |   10000 |         1130274 |
-- |  100000 |         2602517 |
-- | 1000000 |         1164924 |
-- +---------+-----------------+

ALTER TABLE thwiki.logging
  DROP PRIMARY KEY,
  ADD PRIMARY KEY (log_id, log_user)
  PARTITION BY RANGE (log_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p10000 VALUES LESS THAN (10000),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

ALTER TABLE thwiki.revision
  DROP PRIMARY KEY,
  DROP INDEX rev_id,
  ADD PRIMARY KEY (rev_id, rev_user)
  PARTITION BY RANGE (rev_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p10000 VALUES LESS THAN (10000),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

-- trwiki

      select       1 as n, count(rev_user) from trwiki.revision where rev_user  < 1
union select  100000 as n, count(rev_user) from trwiki.revision where rev_user >= 1      and rev_user < 100000
union select  500000 as n, count(rev_user) from trwiki.revision where rev_user >= 100000 and rev_user < 500000
union select 1000000 as n, count(rev_user) from trwiki.revision where rev_user >= 500000 and rev_user < 1000000
union select 2000000 as n, count(rev_user) from trwiki.revision where rev_user >= 1000000;

-- results on 2016-03-08:
-- +---------+-----------------+
-- | n       | count(rev_user) |
-- +---------+-----------------+
-- |       1 |         3160681 |
-- |  100000 |         4153333 |
-- | 1000000 |         7735660 |
-- | 2000000 |               0 |
-- +---------+-----------------+
-- 4 rows in set (18 min 7.94 sec)

ALTER TABLE trwiki.logging
  DROP PRIMARY KEY,
  ADD PRIMARY KEY (log_id, log_user)
  PARTITION BY RANGE (log_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION p500000 VALUES LESS THAN (500000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

ALTER TABLE trwiki.revision
  DROP PRIMARY KEY,
  DROP INDEX rev_id,
  ADD PRIMARY KEY (rev_id, rev_user)
  PARTITION BY RANGE (rev_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION p500000 VALUES LESS THAN (500000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

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

-- results on 2016-03-08:
-- +---------+-----------------+
-- | n       | count(rev_user) |
-- +---------+-----------------+
-- |       1 |         5177460 |
-- |   10000 |         1467357 |
-- |   20000 |         1625075 |
-- |   50000 |         2828562 |
-- |  100000 |         2842176 |
-- |  200000 |         2088287 |
-- |  300000 |         1494092 |
-- |  400000 |         1288781 |
-- |  500000 |         2201698 |
-- | 1000000 |         9437890 |
-- | 2000000 |         5812084 |
-- | 3000000 |          705377 |
-- +---------+-----------------+
-- 12 rows in set (1 min 36.49 sec)

ALTER TABLE zhwiki.logging
  DROP PRIMARY KEY,
  ADD PRIMARY KEY (log_id, log_user)
  PARTITION BY RANGE (log_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p10000 VALUES LESS THAN (10000),
  PARTITION p20000 VALUES LESS THAN (20000),
  PARTITION p50000 VALUES LESS THAN (50000),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION p200000 VALUES LESS THAN (200000),
  PARTITION p300000 VALUES LESS THAN (300000),
  PARTITION p400000 VALUES LESS THAN (400000),
  PARTITION p500000 VALUES LESS THAN (500000),
  PARTITION p750000 VALUES LESS THAN (750000),
  PARTITION p1000000 VALUES LESS THAN (1000000),
  PARTITION p1500000 VALUES LESS THAN (1500000),
  PARTITION p2000000 VALUES LESS THAN (2000000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

ALTER TABLE zhwiki.revision
  DROP PRIMARY KEY,
  DROP INDEX rev_id,
  ADD PRIMARY KEY (rev_id, rev_user)
  PARTITION BY RANGE (rev_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p10000 VALUES LESS THAN (10000),
  PARTITION p20000 VALUES LESS THAN (20000),
  PARTITION p50000 VALUES LESS THAN (50000),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION p200000 VALUES LESS THAN (200000),
  PARTITION p300000 VALUES LESS THAN (300000),
  PARTITION p400000 VALUES LESS THAN (400000),
  PARTITION p500000 VALUES LESS THAN (500000),
  PARTITION p750000 VALUES LESS THAN (750000),
  PARTITION p1000000 VALUES LESS THAN (1000000),
  PARTITION p1500000 VALUES LESS THAN (1500000),
  PARTITION p2000000 VALUES LESS THAN (2000000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );
