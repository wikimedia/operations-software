-- enwiki

      select        1 as n, count(rev_user) from enwiki.revision where rev_user  <        1
union select   100000 as n, count(rev_user) from enwiki.revision where rev_user >=        1 and rev_user <   100000
union select   200000 as n, count(rev_user) from enwiki.revision where rev_user >=   100000 and rev_user <   200000
union select   300000 as n, count(rev_user) from enwiki.revision where rev_user >=   200000 and rev_user <   300000
union select   400000 as n, count(rev_user) from enwiki.revision where rev_user >=   300000 and rev_user <   400000
union select   500000 as n, count(rev_user) from enwiki.revision where rev_user >=   400000 and rev_user <   500000
union select   750000 as n, count(rev_user) from enwiki.revision where rev_user >=   500000 and rev_user <   750000
union select  1000000 as n, count(rev_user) from enwiki.revision where rev_user >=   750000 and rev_user <  1000000
union select  1500000 as n, count(rev_user) from enwiki.revision where rev_user >=  1000000 and rev_user <  1500000
union select  2000000 as n, count(rev_user) from enwiki.revision where rev_user >=  1500000 and rev_user <  2000000
union select  3000000 as n, count(rev_user) from enwiki.revision where rev_user >=  2000000 and rev_user <  3000000
union select  4000000 as n, count(rev_user) from enwiki.revision where rev_user >=  3000000 and rev_user <  4000000
union select  5000000 as n, count(rev_user) from enwiki.revision where rev_user >=  4000000 and rev_user <  5000000
union select  6000000 as n, count(rev_user) from enwiki.revision where rev_user >=  5000000 and rev_user <  6000000
union select  7000000 as n, count(rev_user) from enwiki.revision where rev_user >=  6000000 and rev_user <  7000000
union select  8000000 as n, count(rev_user) from enwiki.revision where rev_user >=  7000000 and rev_user <  8000000
union select  9000000 as n, count(rev_user) from enwiki.revision where rev_user >=  8000000 and rev_user <  9000000
union select 10000000 as n, count(rev_user) from enwiki.revision where rev_user >=  9000000 and rev_user < 10000000
union select 12000000 as n, count(rev_user) from enwiki.revision where rev_user >= 10000000 and rev_user < 12000000
union select 14000000 as n, count(rev_user) from enwiki.revision where rev_user >= 12000000 and rev_user < 14000000
union select 16000000 as n, count(rev_user) from enwiki.revision where rev_user >= 14000000 and rev_user < 16000000
union select 18000000 as n, count(rev_user) from enwiki.revision where rev_user >= 16000000 and rev_user < 18000000
union select 20000000 as n, count(rev_user) from enwiki.revision where rev_user >= 18000000 and rev_user < 30000000;

ALTER TABLE enwiki.logging
  DROP PRIMARY KEY,
  ADD PRIMARY KEY (log_id, log_user)
  PARTITION BY RANGE (log_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION p200000 VALUES LESS THAN (200000),
  PARTITION p300000 VALUES LESS THAN (300000),
  PARTITION p400000 VALUES LESS THAN (400000),
  PARTITION p500000 VALUES LESS THAN (500000),
  PARTITION p700000 VALUES LESS THAN (750000),
  PARTITION p1000000 VALUES LESS THAN (1000000),
  PARTITION p1200000 VALUES LESS THAN (1500000),
  PARTITION p2000000 VALUES LESS THAN (2000000),
  PARTITION p3000000 VALUES LESS THAN (3000000),
  PARTITION p4000000 VALUES LESS THAN (4000000),
  PARTITION p5000000 VALUES LESS THAN (5000000),
  PARTITION p6000000 VALUES LESS THAN (6000000),
  PARTITION p7000000 VALUES LESS THAN (7000000),
  PARTITION p8000000 VALUES LESS THAN (8000000),
  PARTITION p9000000 VALUES LESS THAN (9000000),
  PARTITION p10000000 VALUES LESS THAN (10000000),
  PARTITION p12000000 VALUES LESS THAN (12000000),
  PARTITION p14000000 VALUES LESS THAN (14000000),
  PARTITION p16000000 VALUES LESS THAN (16000000),
  PARTITION p18000000 VALUES LESS THAN (18000000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

ALTER TABLE enwiki.revision
  DROP PRIMARY KEY,
  DROP INDEX rev_id,
  ADD PRIMARY KEY (rev_id, rev_user)
  PARTITION BY RANGE (rev_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION p200000 VALUES LESS THAN (200000),
  PARTITION p300000 VALUES LESS THAN (300000),
  PARTITION p400000 VALUES LESS THAN (400000),
  PARTITION p500000 VALUES LESS THAN (500000),
  PARTITION p700000 VALUES LESS THAN (750000),
  PARTITION p1000000 VALUES LESS THAN (1000000),
  PARTITION p1200000 VALUES LESS THAN (1500000),
  PARTITION p2000000 VALUES LESS THAN (2000000),
  PARTITION p3000000 VALUES LESS THAN (3000000),
  PARTITION p4000000 VALUES LESS THAN (4000000),
  PARTITION p5000000 VALUES LESS THAN (5000000),
  PARTITION p6000000 VALUES LESS THAN (6000000),
  PARTITION p7000000 VALUES LESS THAN (7000000),
  PARTITION p8000000 VALUES LESS THAN (8000000),
  PARTITION p9000000 VALUES LESS THAN (9000000),
  PARTITION p10000000 VALUES LESS THAN (10000000),
  PARTITION p12000000 VALUES LESS THAN (12000000),
  PARTITION p14000000 VALUES LESS THAN (14000000),
  PARTITION p16000000 VALUES LESS THAN (16000000),
  PARTITION p18000000 VALUES LESS THAN (18000000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );
