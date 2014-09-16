-- bgwiki

      select       1 as n, count(rev_user) from bgwiki.revision where rev_user  < 1
union select   10000 as n, count(rev_user) from bgwiki.revision where rev_user >= 1      and rev_user < 10000
union select  100000 as n, count(rev_user) from bgwiki.revision where rev_user >= 10000  and rev_user < 100000
union select 1000000 as n, count(rev_user) from bgwiki.revision where rev_user >= 100000 and rev_user < 1000000;

ALTER TABLE bgwiki.logging
  DROP PRIMARY KEY,
  ADD PRIMARY KEY (log_id, log_user)
  PARTITION BY RANGE (log_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p10000 VALUES LESS THAN (10000),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

ALTER TABLE bgwiki.revision
  DROP PRIMARY KEY,
  DROP INDEX rev_id,
  ADD PRIMARY KEY (rev_id, rev_user)
  PARTITION BY RANGE (rev_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p10000 VALUES LESS THAN (10000),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

-- cswiki

      select       1 as n, count(rev_user) from cswiki.revision where rev_user  < 1
union select   10000 as n, count(rev_user) from cswiki.revision where rev_user >= 1      and rev_user < 10000
union select  100000 as n, count(rev_user) from cswiki.revision where rev_user >= 10000  and rev_user < 100000
union select 1000000 as n, count(rev_user) from cswiki.revision where rev_user >= 100000 and rev_user < 1000000;

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
union select 1000000 as n, count(rev_user) from enwikiquote.revision where rev_user >= 100000 and rev_user < 1000000;

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
union select 2000000 as n, count(rev_user) from enwiktionary.revision where rev_user >= 1000000 and rev_user < 2000000;

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
  PARTITION p400000 VALUES LESS THAN (400000),
  PARTITION p500000 VALUES LESS THAN (500000),
  PARTITION p1000000 VALUES LESS THAN (1000000),
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
  PARTITION p400000 VALUES LESS THAN (400000),
  PARTITION p500000 VALUES LESS THAN (500000),
  PARTITION p1000000 VALUES LESS THAN (1000000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

-- fiwiki

      select       1 as n, count(rev_user) from fiwiki.revision where rev_user  < 1
union select   10000 as n, count(rev_user) from fiwiki.revision where rev_user >= 1      and rev_user < 10000
union select  100000 as n, count(rev_user) from fiwiki.revision where rev_user >= 10000  and rev_user < 100000
union select 1000000 as n, count(rev_user) from fiwiki.revision where rev_user >= 100000 and rev_user < 1000000;

ALTER TABLE fiwiki.logging
  DROP PRIMARY KEY,
  ADD PRIMARY KEY (log_id, log_user)
  PARTITION BY RANGE (log_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p10000 VALUES LESS THAN (10000),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

ALTER TABLE fiwiki.revision
  DROP PRIMARY KEY,
  DROP INDEX rev_id,
  ADD PRIMARY KEY (rev_id, rev_user)
  PARTITION BY RANGE (rev_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p10000 VALUES LESS THAN (10000),
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
union select 2000000 as n, count(rev_user) from itwiki.revision where rev_user >= 1000000 and rev_user < 2000000;

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
  PARTITION p200000 VALUES LESS THAN (200000),
  PARTITION p300000 VALUES LESS THAN (300000),
  PARTITION p400000 VALUES LESS THAN (400000),
  PARTITION p500000 VALUES LESS THAN (500000),
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
  PARTITION p200000 VALUES LESS THAN (200000),
  PARTITION p300000 VALUES LESS THAN (300000),
  PARTITION p400000 VALUES LESS THAN (400000),
  PARTITION p500000 VALUES LESS THAN (500000),
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
union select 1000000 as n, count(rev_user) from nlwiki.revision where rev_user >= 500000  and rev_user < 1000000;

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
  PARTITION p200000 VALUES LESS THAN (200000),
  PARTITION p300000 VALUES LESS THAN (300000),
  PARTITION p400000 VALUES LESS THAN (400000),
  PARTITION p500000 VALUES LESS THAN (500000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

-- nowiki

      select       1 as n, count(rev_user) from nowiki.revision where rev_user  < 1
union select   10000 as n, count(rev_user) from nowiki.revision where rev_user >= 1      and rev_user < 10000
union select  100000 as n, count(rev_user) from nowiki.revision where rev_user >= 10000  and rev_user < 100000
union select 1000000 as n, count(rev_user) from nowiki.revision where rev_user >= 100000 and rev_user < 1000000;

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
union select 1000000 as n, count(rev_user) from plwiki.revision where rev_user >= 500000  and rev_user < 1000000;

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
  PARTITION p100000 VALUES LESS THAN (100000),
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
  PARTITION p100000 VALUES LESS THAN (100000),
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
union select 2000000 as n, count(rev_user) from ptwiki.revision where rev_user >= 1000000 and rev_user < 2000000;

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
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

-- svwiki

      select       1 as n, count(rev_user) from svwiki.revision where rev_user  < 1
union select   10000 as n, count(rev_user) from svwiki.revision where rev_user >= 1       and rev_user <   10000
union select   50000 as n, count(rev_user) from svwiki.revision where rev_user >= 10000   and rev_user <   50000
union select  100000 as n, count(rev_user) from svwiki.revision where rev_user >= 50000   and rev_user <  100000
union select  200000 as n, count(rev_user) from svwiki.revision where rev_user >= 100000  and rev_user <  200000
union select  300000 as n, count(rev_user) from svwiki.revision where rev_user >= 200000  and rev_user <  300000
union select 1000000 as n, count(rev_user) from svwiki.revision where rev_user >= 300000  and rev_user < 1000000;

ALTER TABLE svwiki.logging
  DROP PRIMARY KEY,
  ADD PRIMARY KEY (log_id, log_user)
  PARTITION BY RANGE (log_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p10000 VALUES LESS THAN (10000),
  PARTITION p50000 VALUES LESS THAN (50000),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION p200000 VALUES LESS THAN (200000),
  PARTITION p300000 VALUES LESS THAN (300000),
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
  PARTITION p300000 VALUES LESS THAN (300000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

-- thwiki

      select       1 as n, count(rev_user) from thwiki.revision where rev_user  < 1
union select   10000 as n, count(rev_user) from thwiki.revision where rev_user >= 1      and rev_user < 10000
union select  100000 as n, count(rev_user) from thwiki.revision where rev_user >= 10000  and rev_user < 100000
union select 1000000 as n, count(rev_user) from thwiki.revision where rev_user >= 100000 and rev_user < 1000000;

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
union select 1000000 as n, count(rev_user) from trwiki.revision where rev_user >= 100000 and rev_user < 1000000;

ALTER TABLE trwiki.logging
  DROP PRIMARY KEY,
  ADD PRIMARY KEY (log_id, log_user)
  PARTITION BY RANGE (log_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

ALTER TABLE trwiki.revision
  DROP PRIMARY KEY,
  DROP INDEX rev_id,
  ADD PRIMARY KEY (rev_id, rev_user)
  PARTITION BY RANGE (rev_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p100000 VALUES LESS THAN (100000),
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
union select 2000000 as n, count(rev_user) from zhwiki.revision where rev_user >= 1000000 and rev_user < 2000000;

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
  PARTITION p1000000 VALUES LESS THAN (1000000),
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
  PARTITION p1000000 VALUES LESS THAN (1000000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );