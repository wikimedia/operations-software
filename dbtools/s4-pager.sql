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
-- results on 2016-07-06:
-- 
-- +---------+-----------------+
-- | n       | count(rev_user) |
-- +---------+-----------------+
-- |       1 |         2467291 |
-- |   10000 |        11701314 |
-- |   20000 |         5551361 |
-- |   30000 |         3695045 |
-- |   40000 |         2637797 |
-- |   50000 |         5223923 |
-- |  100000 |        15495476 |
-- |  200000 |        17436977 |
-- |  300000 |        13942075 |
-- |  400000 |        15903408 |
-- |  500000 |         6163418 |
-- | 1000000 |        21067980 |
-- | 2000000 |        32877326 |
-- | 3000000 |         9822336 |
-- | 4000000 |        17395118 |
-- | 9999999 |         5647314 |
-- +---------+-----------------+
-- 16 rows in set (29 min 4.75 sec)

ALTER TABLE commonswiki.logging
  DROP PRIMARY KEY,
  ADD PRIMARY KEY (log_id, log_user)
  PARTITION BY RANGE (log_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p5000 VALUES LESS THAN (5000),
  PARTITION p10000 VALUES LESS THAN (10000),
  PARTITION p20000 VALUES LESS THAN (20000),
  PARTITION p30000 VALUES LESS THAN (30000),
  PARTITION p40000 VALUES LESS THAN (40000),
  PARTITION p50000 VALUES LESS THAN (50000),
  PARTITION p75000 VALUES LESS THAN (75000),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION p150000 VALUES LESS THAN (150000),
  PARTITION p200000 VALUES LESS THAN (200000),
  PARTITION p250000 VALUES LESS THAN (250000),
  PARTITION p300000 VALUES LESS THAN (300000),
  PARTITION p350000 VALUES LESS THAN (350000),
  PARTITION p400000 VALUES LESS THAN (400000),
  PARTITION p500000 VALUES LESS THAN (500000),
  PARTITION p750000 VALUES LESS THAN (750000),
  PARTITION p1000000 VALUES LESS THAN (1000000),
  PARTITION p1500000 VALUES LESS THAN (1500000),
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
  PARTITION p5000 VALUES LESS THAN (5000),
  PARTITION p10000 VALUES LESS THAN (10000),
  PARTITION p20000 VALUES LESS THAN (20000),
  PARTITION p30000 VALUES LESS THAN (30000),
  PARTITION p40000 VALUES LESS THAN (40000),
  PARTITION p50000 VALUES LESS THAN (50000),
  PARTITION p75000 VALUES LESS THAN (75000),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION p150000 VALUES LESS THAN (150000),
  PARTITION p200000 VALUES LESS THAN (200000),
  PARTITION p250000 VALUES LESS THAN (250000),
  PARTITION p300000 VALUES LESS THAN (300000),
  PARTITION p350000 VALUES LESS THAN (350000),
  PARTITION p400000 VALUES LESS THAN (400000),
  PARTITION p500000 VALUES LESS THAN (500000),
  PARTITION p750000 VALUES LESS THAN (750000),
  PARTITION p1000000 VALUES LESS THAN (1000000),
  PARTITION p1500000 VALUES LESS THAN (1500000),
  PARTITION p2000000 VALUES LESS THAN (2000000),
  PARTITION p3000000 VALUES LESS THAN (3000000),
  PARTITION p4000000 VALUES LESS THAN (4000000),
  PARTITION p5000000 VALUES LESS THAN (5000000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

