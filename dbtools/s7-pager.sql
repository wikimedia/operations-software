-- arwiki

      select       1 as n, count(rev_user) from arwiki.revision where rev_user  < 1
union select  100000 as n, count(rev_user) from arwiki.revision where rev_user >= 1       and rev_user < 100000
union select  150000 as n, count(rev_user) from arwiki.revision where rev_user >= 100000  and rev_user < 150000
union select  250000 as n, count(rev_user) from arwiki.revision where rev_user >= 150000  and rev_user < 250000
union select 1000000 as n, count(rev_user) from arwiki.revision where rev_user >= 250000  and rev_user < 1000000
union select 2000000 as n, count(rev_user) from arwiki.revision where rev_user >= 1000000 and rev_user < 2000000;

ALTER TABLE arwiki.logging
  DROP PRIMARY KEY,
  ADD PRIMARY KEY (log_id, log_user)
  PARTITION BY RANGE (log_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION p150000 VALUES LESS THAN (150000),
  PARTITION p250000 VALUES LESS THAN (250000),
  PARTITION p1000000 VALUES LESS THAN (1000000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

ALTER TABLE arwiki.revision
  DROP PRIMARY KEY,
  DROP INDEX rev_id,
  ADD PRIMARY KEY (rev_id, rev_user)
  PARTITION BY RANGE (rev_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION p150000 VALUES LESS THAN (150000),
  PARTITION p250000 VALUES LESS THAN (250000),
  PARTITION p1000000 VALUES LESS THAN (1000000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

-- cawiki

      select       1 as n, count(rev_user) from cawiki.revision where rev_user  < 1
union select   10000 as n, count(rev_user) from cawiki.revision where rev_user >= 1       and rev_user < 10000
union select 1000000 as n, count(rev_user) from cawiki.revision where rev_user >= 10000   and rev_user < 1000000;

ALTER TABLE cawiki.logging
  DROP PRIMARY KEY,
  ADD PRIMARY KEY (log_id, log_user)
  PARTITION BY RANGE (log_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p10000 VALUES LESS THAN (10000),
  PARTITION p1000000 VALUES LESS THAN (1000000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

ALTER TABLE cawiki.revision
  DROP PRIMARY KEY,
  DROP INDEX rev_id,
  ADD PRIMARY KEY (rev_id, rev_user)
  PARTITION BY RANGE (rev_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p10000 VALUES LESS THAN (10000),
  PARTITION p1000000 VALUES LESS THAN (1000000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

-- eswiki

      select       1 as n, count(rev_user) from eswiki.revision where rev_user  < 1
union select   10000 as n, count(rev_user) from eswiki.revision where rev_user >= 1       and rev_user < 10000
union select  100000 as n, count(rev_user) from eswiki.revision where rev_user >= 10000   and rev_user < 100000
union select  200000 as n, count(rev_user) from eswiki.revision where rev_user >= 100000  and rev_user < 200000
union select  300000 as n, count(rev_user) from eswiki.revision where rev_user >= 200000  and rev_user < 300000
union select  400000 as n, count(rev_user) from eswiki.revision where rev_user >= 300000  and rev_user < 400000
union select  500000 as n, count(rev_user) from eswiki.revision where rev_user >= 400000  and rev_user < 500000
union select 1000000 as n, count(rev_user) from eswiki.revision where rev_user >= 500000  and rev_user < 1000000
union select 2000000 as n, count(rev_user) from eswiki.revision where rev_user >= 1000000 and rev_user < 2000000
union select 3000000 as n, count(rev_user) from eswiki.revision where rev_user >= 2000000 and rev_user < 3000000;

ALTER TABLE eswiki.logging
  DROP PRIMARY KEY,
  ADD PRIMARY KEY (log_id, log_user)
  PARTITION BY RANGE (log_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p10000 VALUES LESS THAN (10000),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION p200000 VALUES LESS THAN (200000),
  PARTITION p300000 VALUES LESS THAN (300000),
  PARTITION p400000 VALUES LESS THAN (400000),
  PARTITION p500000 VALUES LESS THAN (500000),
  PARTITION p1000000 VALUES LESS THAN (1000000),
  PARTITION p2000000 VALUES LESS THAN (2000000),
  PARTITION p3000000 VALUES LESS THAN (3000000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

ALTER TABLE eswiki.revision
  DROP PRIMARY KEY,
  DROP INDEX rev_id,
  ADD PRIMARY KEY (rev_id, rev_user)
  PARTITION BY RANGE (rev_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p10000 VALUES LESS THAN (10000),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION p200000 VALUES LESS THAN (200000),
  PARTITION p300000 VALUES LESS THAN (300000),
  PARTITION p400000 VALUES LESS THAN (400000),
  PARTITION p500000 VALUES LESS THAN (500000),
  PARTITION p1000000 VALUES LESS THAN (1000000),
  PARTITION p2000000 VALUES LESS THAN (2000000),
  PARTITION p3000000 VALUES LESS THAN (3000000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

-- fawiki

      select       1 as n, count(rev_user) from fawiki.revision where rev_user  < 1
union select   10000 as n, count(rev_user) from fawiki.revision where rev_user >= 1       and rev_user < 10000
union select   10000 as n, count(rev_user) from fawiki.revision where rev_user >= 10000   and rev_user < 100000
union select   10000 as n, count(rev_user) from fawiki.revision where rev_user >= 100000  and rev_user < 200000
union select   10000 as n, count(rev_user) from fawiki.revision where rev_user >= 200000  and rev_user < 300000
union select   10000 as n, count(rev_user) from fawiki.revision where rev_user >= 300000  and rev_user < 400000
union select 1000000 as n, count(rev_user) from fawiki.revision where rev_user >= 400000  and rev_user < 1000000;

ALTER TABLE fawiki.logging
  DROP PRIMARY KEY,
  ADD PRIMARY KEY (log_id, log_user)
  PARTITION BY RANGE (log_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p10000 VALUES LESS THAN (10000),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION p200000 VALUES LESS THAN (200000),
  PARTITION p300000 VALUES LESS THAN (300000),
  PARTITION p400000 VALUES LESS THAN (400000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

ALTER TABLE fawiki.revision
  DROP PRIMARY KEY,
  DROP INDEX rev_id,
  ADD PRIMARY KEY (rev_id, rev_user)
  PARTITION BY RANGE (rev_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p10000 VALUES LESS THAN (10000),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION p200000 VALUES LESS THAN (200000),
  PARTITION p300000 VALUES LESS THAN (300000),
  PARTITION p400000 VALUES LESS THAN (400000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

-- hewiki

      select       1 as n, count(rev_user) from hewiki.revision where rev_user  < 1
union select  100000 as n, count(rev_user) from hewiki.revision where rev_user >= 1       and rev_user < 100000
union select 1000000 as n, count(rev_user) from hewiki.revision where rev_user >= 100000  and rev_user < 1000000;

ALTER TABLE hewiki.logging
  DROP PRIMARY KEY,
  ADD PRIMARY KEY (log_id, log_user)
  PARTITION BY RANGE (log_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

ALTER TABLE hewiki.revision
  DROP PRIMARY KEY,
  DROP INDEX rev_id,
  ADD PRIMARY KEY (rev_id, rev_user)
  PARTITION BY RANGE (rev_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

-- huwiki

      select       1 as n, count(rev_user) from huwiki.revision where rev_user  < 1
union select  100000 as n, count(rev_user) from huwiki.revision where rev_user >= 1       and rev_user < 100000
union select 1000000 as n, count(rev_user) from huwiki.revision where rev_user >= 100000  and rev_user < 1000000;

ALTER TABLE huwiki.logging
  DROP PRIMARY KEY,
  ADD PRIMARY KEY (log_id, log_user)
  PARTITION BY RANGE (log_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

ALTER TABLE huwiki.revision
  DROP PRIMARY KEY,
  DROP INDEX rev_id,
  ADD PRIMARY KEY (rev_id, rev_user)
  PARTITION BY RANGE (rev_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

-- kowiki

      select       1 as n, count(rev_user) from kowiki.revision where rev_user  < 1
union select  100000 as n, count(rev_user) from kowiki.revision where rev_user >= 1       and rev_user < 100000
union select 1000000 as n, count(rev_user) from kowiki.revision where rev_user >= 100000  and rev_user < 1000000;

ALTER TABLE kowiki.logging
  DROP PRIMARY KEY,
  ADD PRIMARY KEY (log_id, log_user)
  PARTITION BY RANGE (log_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

ALTER TABLE kowiki.revision
  DROP PRIMARY KEY,
  DROP INDEX rev_id,
  ADD PRIMARY KEY (rev_id, rev_user)
  PARTITION BY RANGE (rev_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

-- metawiki

      select       1 as n, count(rev_user) from metawiki.revision where rev_user  < 1
union select  100000 as n, count(rev_user) from metawiki.revision where rev_user >= 1       and rev_user < 100000
union select  500000 as n, count(rev_user) from metawiki.revision where rev_user >= 100000  and rev_user < 500000
union select 1000000 as n, count(rev_user) from metawiki.revision where rev_user >= 500000  and rev_user < 1000000
union select 9000000 as n, count(rev_user) from metawiki.revision where rev_user >= 1000000 and rev_user < 9000000;

ALTER TABLE metawiki.logging
  DROP PRIMARY KEY,
  ADD PRIMARY KEY (log_id, log_user)
  PARTITION BY RANGE (log_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION p500000 VALUES LESS THAN (500000),
  PARTITION p1000000 VALUES LESS THAN (1000000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

ALTER TABLE metawiki.revision
  DROP PRIMARY KEY,
  DROP INDEX rev_id,
  ADD PRIMARY KEY (rev_id, rev_user)
  PARTITION BY RANGE (rev_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION p500000 VALUES LESS THAN (500000),
  PARTITION p1000000 VALUES LESS THAN (1000000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

-- rowiki

      select       1 as n, count(rev_user) from rowiki.revision where rev_user  < 1
union select  100000 as n, count(rev_user) from rowiki.revision where rev_user >= 1       and rev_user < 100000
union select 1000000 as n, count(rev_user) from rowiki.revision where rev_user >= 100000  and rev_user < 1000000;

ALTER TABLE rowiki.logging
  DROP PRIMARY KEY,
  ADD PRIMARY KEY (log_id, log_user)
  PARTITION BY RANGE (log_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

ALTER TABLE rowiki.revision
  DROP PRIMARY KEY,
  DROP INDEX rev_id,
  ADD PRIMARY KEY (rev_id, rev_user)
  PARTITION BY RANGE (rev_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

-- ukwiki

      select       1 as n, count(rev_user) from ukwiki.revision where rev_user  < 1
union select  100000 as n, count(rev_user) from ukwiki.revision where rev_user >= 1       and rev_user < 100000
union select 1000000 as n, count(rev_user) from ukwiki.revision where rev_user >= 100000  and rev_user < 1000000;

ALTER TABLE ukwiki.logging
  DROP PRIMARY KEY,
  ADD PRIMARY KEY (log_id, log_user)
  PARTITION BY RANGE (log_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

ALTER TABLE ukwiki.revision
  DROP PRIMARY KEY,
  DROP INDEX rev_id,
  ADD PRIMARY KEY (rev_id, rev_user)
  PARTITION BY RANGE (rev_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

-- viwiki

      select       1 as n, count(rev_user) from viwiki.revision where rev_user  < 1
union select  100000 as n, count(rev_user) from viwiki.revision where rev_user >= 1       and rev_user < 100000
union select  200000 as n, count(rev_user) from viwiki.revision where rev_user >= 100000  and rev_user < 200000
union select  300000 as n, count(rev_user) from viwiki.revision where rev_user >= 200000  and rev_user < 300000
union select 1000000 as n, count(rev_user) from viwiki.revision where rev_user >= 300000  and rev_user < 1000000;

ALTER TABLE viwiki.logging
  DROP PRIMARY KEY,
  ADD PRIMARY KEY (log_id, log_user)
  PARTITION BY RANGE (log_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION p200000 VALUES LESS THAN (200000),
  PARTITION p300000 VALUES LESS THAN (300000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

ALTER TABLE viwiki.revision
  DROP PRIMARY KEY,
  DROP INDEX rev_id,
  ADD PRIMARY KEY (rev_id, rev_user)
  PARTITION BY RANGE (rev_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION p200000 VALUES LESS THAN (200000),
  PARTITION p300000 VALUES LESS THAN (300000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );
