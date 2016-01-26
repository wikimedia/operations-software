-- commonswiki

      select       1 as n, count(rev_user) from commonswiki.revision where rev_user  < 1
union select   10000 as n, count(rev_user) from commonswiki.revision where rev_user >= 1       and rev_user <  10000
union select   20000 as n, count(rev_user) from commonswiki.revision where rev_user >= 10000   and rev_user <  20000
union select   30000 as n, count(rev_user) from commonswiki.revision where rev_user >= 20000   and rev_user <  30000
union select   40000 as n, count(rev_user) from commonswiki.revision where rev_user >= 30000   and rev_user <  40000
union select   50000 as n, count(rev_user) from commonswiki.revision where rev_user >= 40000   and rev_user <  50000
union select  100000 as n, count(rev_user) from commonswiki.revision where rev_user >= 50000   and rev_user < 100000
union select  200000 as n, count(rev_user) from commonswiki.revision where rev_user >= 100000  and rev_user < 200000
union select  300000 as n, count(rev_user) from commonswiki.revision where rev_user >= 200000  and rev_user < 300000
union select  400000 as n, count(rev_user) from commonswiki.revision where rev_user >= 300000  and rev_user < 400000
union select  500000 as n, count(rev_user) from commonswiki.revision where rev_user >= 400000  and rev_user < 500000
union select 1000000 as n, count(rev_user) from commonswiki.revision where rev_user >= 500000  and rev_user < 1000000
union select 2000000 as n, count(rev_user) from commonswiki.revision where rev_user >= 1000000 and rev_user < 2000000
union select 3000000 as n, count(rev_user) from commonswiki.revision where rev_user >= 2000000 and rev_user < 3000000
union select 4000000 as n, count(rev_user) from commonswiki.revision where rev_user >= 3000000 and rev_user < 4000000
union select 9999999 as n, count(rev_user) from commonswiki.revision where rev_user >= 4000000;

-- 
-- results on 2015-12-29:
-- 
-- +---------+-----------------+
-- | n       | count(rev_user) |
-- +---------+-----------------+
-- |       1 |         2312096 |
-- |   10000 |        11038216 |
-- |   20000 |         5254160 |
-- |   30000 |         3460782 |
-- |   40000 |         2351946 |
-- |   50000 |         4844739 |
-- |  100000 |        14958145 |
-- |  200000 |        16239187 |
-- |  300000 |        13011323 |
-- |  400000 |        14644094 |
-- |  500000 |         5853173 |
-- | 1000000 |        19852423 |
-- | 2000000 |        29449241 |
-- | 3000000 |         8517747 |
-- | 4000000 |        15687869 |
-- | 5000000 |         2938461 |
-- +---------+-----------------+
-- 16 rows in set (10 min 23.22 sec)

ALTER TABLE commonswiki.logging
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
  PARTITION p750000 VALUES LESS THAN (750000),
  PARTITION p1000000 VALUES LESS THAN (1000000),
  PARTITION p2000000 VALUES LESS THAN (2000000),
  PARTITION p3000000 VALUES LESS THAN (3000000),
  PARTITION p4000000 VALUES LESS THAN (4000000),
  PARTITION p5000000 VALUES LESS THAN (5000000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

ALTER TABLE commonswiki.revision
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
  PARTITION p750000 VALUES LESS THAN (750000),
  PARTITION p1000000 VALUES LESS THAN (1000000),
  PARTITION p2000000 VALUES LESS THAN (2000000),
  PARTITION p3000000 VALUES LESS THAN (3000000),
  PARTITION p4000000 VALUES LESS THAN (4000000),
  PARTITION p5000000 VALUES LESS THAN (5000000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

