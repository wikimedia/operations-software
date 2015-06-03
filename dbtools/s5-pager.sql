-- dewiki

      select       1 as n, count(rev_user) from dewiki.revision where rev_user  < 1
union select   10000 as n, count(rev_user) from dewiki.revision where rev_user >= 1       and rev_user < 10000
union select   20000 as n, count(rev_user) from dewiki.revision where rev_user >= 10000   and rev_user < 20000
union select   30000 as n, count(rev_user) from dewiki.revision where rev_user >= 20000   and rev_user < 30000
union select  100000 as n, count(rev_user) from dewiki.revision where rev_user >= 30000   and rev_user < 100000
union select  200000 as n, count(rev_user) from dewiki.revision where rev_user >= 100000  and rev_user < 200000
union select  300000 as n, count(rev_user) from dewiki.revision where rev_user >= 200000  and rev_user < 300000
union select 1000000 as n, count(rev_user) from dewiki.revision where rev_user >= 300000  and rev_user < 1000000
union select 2000000 as n, count(rev_user) from dewiki.revision where rev_user >= 1000000 and rev_user < 2000000;

ALTER TABLE dewiki.logging
  DROP PRIMARY KEY,
  ADD PRIMARY KEY (log_id, log_user)
  PARTITION BY RANGE (log_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p10000 VALUES LESS THAN (10000),
  PARTITION p20000 VALUES LESS THAN (20000),
  PARTITION p50000 VALUES LESS THAN (30000),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION p200000 VALUES LESS THAN (200000),
  PARTITION p300000 VALUES LESS THAN (300000),
  PARTITION p1000000 VALUES LESS THAN (1000000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

ALTER TABLE dewiki.revision
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
  PARTITION p1000000 VALUES LESS THAN (1000000),
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
union select 2000000 as n, count(rev_user) from wikidatawiki.revision where rev_user >= 1000000 and rev_user < 2000000;

ALTER TABLE wikidatawiki.logging
  DROP PRIMARY KEY,
  ADD PRIMARY KEY (log_id, log_user)
  PARTITION BY RANGE (log_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p10000 VALUES LESS THAN (10000),
  PARTITION p20000 VALUES LESS THAN (20000),
  PARTITION p30000 VALUES LESS THAN (30000),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION p200000 VALUES LESS THAN (200000),
  PARTITION p300000 VALUES LESS THAN (300000),
  PARTITION p1000000 VALUES LESS THAN (1000000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

ALTER TABLE wikidatawiki.revision
  DROP PRIMARY KEY,
  ADD PRIMARY KEY (rev_id, rev_user)
  PARTITION BY RANGE (rev_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p10000 VALUES LESS THAN (10000),
  PARTITION p20000 VALUES LESS THAN (20000),
  PARTITION p30000 VALUES LESS THAN (30000),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION p200000 VALUES LESS THAN (200000),
  PARTITION p300000 VALUES LESS THAN (300000),
  PARTITION p1000000 VALUES LESS THAN (1000000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );