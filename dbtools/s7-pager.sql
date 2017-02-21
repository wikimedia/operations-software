-- arwiki

      select       1 as n, count(rev_user) from arwiki.revision where rev_user  < 1
union select  100000 as n, count(rev_user) from arwiki.revision where rev_user >= 1       and rev_user < 100000
union select  150000 as n, count(rev_user) from arwiki.revision where rev_user >= 100000  and rev_user < 150000
union select  250000 as n, count(rev_user) from arwiki.revision where rev_user >= 150000  and rev_user < 250000
union select 1000000 as n, count(rev_user) from arwiki.revision where rev_user >= 250000  and rev_user < 1000000
union select 2000000 as n, count(rev_user) from arwiki.revision where rev_user >= 1000000 and rev_user < 2000000;

-- results on 2016-03-08:
-- +---------+-----------------+
-- | n       | count(rev_user) |
-- +---------+-----------------+
-- |       1 |         1560336 |
-- |  100000 |         3897959 |
-- |  150000 |         2807094 |
-- |  250000 |         1931252 |
-- | 1000000 |         6394709 |
-- | 2000000 |          522743 |
-- +---------+-----------------+
-- 6 rows in set (3 min 17.17 sec)

ALTER TABLE arwiki.logging
  DROP PRIMARY KEY,
  ADD PRIMARY KEY (log_id, log_user)
  PARTITION BY RANGE (log_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION p150000 VALUES LESS THAN (150000),
  PARTITION p250000 VALUES LESS THAN (250000),
  PARTITION p500000 VALUES LESS THAN (500000),
  PARTITION p750000 VALUES LESS THAN (750000),
  PARTITION p1000000 VALUES LESS THAN (1000000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

ALTER TABLE arwiki.revision
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
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION p150000 VALUES LESS THAN (150000),
  PARTITION p250000 VALUES LESS THAN (250000),
  PARTITION p500000 VALUES LESS THAN (500000),
  PARTITION p750000 VALUES LESS THAN (750000),
  PARTITION p1000000 VALUES LESS THAN (1000000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

-- cawiki

      select       1 as n, count(rev_user) from cawiki.revision where rev_user  < 1
union select   10000 as n, count(rev_user) from cawiki.revision where rev_user >= 1       and rev_user < 10000
union select  100000 as n, count(rev_user) from cawiki.revision where rev_user >= 10000   and rev_user < 100000
union select 1000000 as n, count(rev_user) from cawiki.revision where rev_user >= 1000000;

-- results on 2016-03-08:
-- +---------+-----------------+
-- | n       | count(rev_user) |
-- +---------+-----------------+
-- |       1 |          707685 |
-- |   10000 |         6027668 |
-- |  100000 |         6677736 |
-- | 1000000 |               0 |
-- +---------+-----------------+
-- 4 rows in set (4.55 sec)

ALTER TABLE cawiki.logging
  DROP PRIMARY KEY,
  ADD PRIMARY KEY (log_id, log_user)
  PARTITION BY RANGE (log_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p5000 VALUES LESS THAN (5000),
  PARTITION p10000 VALUES LESS THAN (10000),
  PARTITION p50000 VALUES LESS THAN (50000),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION p1000000 VALUES LESS THAN (1000000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

ALTER TABLE cawiki.revision
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
  PARTITION p50000 VALUES LESS THAN (50000),
  PARTITION p100000 VALUES LESS THAN (100000),
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
union select 3000000 as n, count(rev_user) from eswiki.revision where rev_user >= 2000000 and rev_user < 3000000
union select 4000000 as n, count(rev_user) from eswiki.revision where rev_user >= 3000000;

-- results on 2016-03-08:
-- +---------+-----------------+
-- | n       | count(rev_user) |
-- +---------+-----------------+
-- |       1 |        22099484 |
-- |   10000 |          678909 |
-- |  100000 |         8771273 |
-- |  200000 |         4655450 |
-- |  300000 |         4801932 |
-- |  400000 |         4414710 |
-- |  500000 |         2976735 |
-- | 1000000 |        11482887 |
-- | 2000000 |        13695498 |
-- | 3000000 |         6114337 |
-- | 4000000 |         2636962 |
-- +---------+-----------------+
-- 11 rows in set (20 min 41.20 sec)

ALTER TABLE eswiki.logging
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
  PARTITION p600000 VALUES LESS THAN (600000),
  PARTITION p700000 VALUES LESS THAN (700000),
  PARTITION p800000 VALUES LESS THAN (800000),
  PARTITION p900000 VALUES LESS THAN (900000),
  PARTITION p1000000 VALUES LESS THAN (1000000),
  PARTITION p1250000 VALUES LESS THAN (1250000),
  PARTITION p1500000 VALUES LESS THAN (1500000),
  PARTITION p1750000 VALUES LESS THAN (1750000),
  PARTITION p2000000 VALUES LESS THAN (2000000),
  PARTITION p2500000 VALUES LESS THAN (2500000),
  PARTITION p3000000 VALUES LESS THAN (3000000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

ALTER TABLE eswiki.revision
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
  PARTITION p10000 VALUES LESS THAN (10000),
  PARTITION p50000 VALUES LESS THAN (50000),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION p200000 VALUES LESS THAN (200000),
  PARTITION p300000 VALUES LESS THAN (300000),
  PARTITION p400000 VALUES LESS THAN (400000),
  PARTITION p500000 VALUES LESS THAN (500000),
  PARTITION p600000 VALUES LESS THAN (600000),
  PARTITION p700000 VALUES LESS THAN (700000),
  PARTITION p800000 VALUES LESS THAN (800000),
  PARTITION p900000 VALUES LESS THAN (900000),
  PARTITION p1000000 VALUES LESS THAN (1000000),
  PARTITION p1250000 VALUES LESS THAN (1250000),
  PARTITION p1500000 VALUES LESS THAN (1500000),
  PARTITION p1750000 VALUES LESS THAN (1750000),
  PARTITION p2000000 VALUES LESS THAN (2000000),
  PARTITION p2500000 VALUES LESS THAN (2500000),
  PARTITION p3000000 VALUES LESS THAN (3000000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

-- fawiki

      select       1 as n, count(rev_user) from fawiki.revision where rev_user  < 1
union select   10000 as n, count(rev_user) from fawiki.revision where rev_user >= 1       and rev_user < 10000
union select  100000 as n, count(rev_user) from fawiki.revision where rev_user >= 10000   and rev_user < 100000
union select  200000 as n, count(rev_user) from fawiki.revision where rev_user >= 100000  and rev_user < 200000
union select  300000 as n, count(rev_user) from fawiki.revision where rev_user >= 200000  and rev_user < 300000
union select  400000 as n, count(rev_user) from fawiki.revision where rev_user >= 300000  and rev_user < 400000
union select 1000000 as n, count(rev_user) from fawiki.revision where rev_user >= 400000  and rev_user < 1000000
union select 1500000 as n, count(rev_user) from fawiki.revision where rev_user >= 1000000;

-- results on 2016-03-08:
-- +---------+-----------------+
-- | n       | count(rev_user) |
-- +---------+-----------------+
-- |       1 |          596773 |
-- |   10000 |         1275757 |
-- |  100000 |         2584518 |
-- |  200000 |         3218661 |
-- |  300000 |         5986679 |
-- |  400000 |         1245870 |
-- | 1000000 |          597698 |
-- | 1500000 |               0 |
-- +---------+-----------------+
-- 8 rows in set (4 min 11.96 sec)

ALTER TABLE fawiki.logging
  DROP PRIMARY KEY,
  ADD PRIMARY KEY (log_id, log_user)
  PARTITION BY RANGE (log_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p10000 VALUES LESS THAN (10000),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION p200000 VALUES LESS THAN (200000),
  PARTITION p250000 VALUES LESS THAN (250000),
  PARTITION p300000 VALUES LESS THAN (300000),
  PARTITION p400000 VALUES LESS THAN (400000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

ALTER TABLE fawiki.revision
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
  PARTITION p10000 VALUES LESS THAN (10000),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION p200000 VALUES LESS THAN (200000),
  PARTITION p250000 VALUES LESS THAN (250000),
  PARTITION p300000 VALUES LESS THAN (300000),
  PARTITION p400000 VALUES LESS THAN (400000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

-- hewiki

      select       1 as n, count(rev_user) from hewiki.revision where rev_user  < 1
union select   10000 as n, count(rev_user) from hewiki.revision where rev_user >= 1       and rev_user < 10000
union select  100000 as n, count(rev_user) from hewiki.revision where rev_user >= 10000   and rev_user < 100000
union select 1000000 as n, count(rev_user) from hewiki.revision where rev_user >= 100000  and rev_user < 1000000
union select 10000000 as n, count(rev_user) from hewiki.revision where rev_user >= 1000000;

-- results on 2016-03-08:
-- +----------+-----------------+
-- | n        | count(rev_user) |
-- +----------+-----------------+
-- |        1 |         1678783 |
-- |    10000 |         3468628 |
-- |   100000 |         8169245 |
-- |  1000000 |         3654690 |
-- | 10000000 |               0 |
-- +----------+-----------------+
-- 5 rows in set (5 min 26.17 sec)

ALTER TABLE hewiki.logging
  DROP PRIMARY KEY,
  ADD PRIMARY KEY (log_id, log_user)
  PARTITION BY RANGE (log_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p10000 VALUES LESS THAN (10000),
  PARTITION p50000 VALUES LESS THAN (50000),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION p1000000 VALUES LESS THAN (1000000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

ALTER TABLE hewiki.revision
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
  PARTITION p10000 VALUES LESS THAN (10000),
  PARTITION p50000 VALUES LESS THAN (50000),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION p1000000 VALUES LESS THAN (1000000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

-- huwiki

      select       1 as n, count(rev_user) from huwiki.revision where rev_user  < 1
union select   10000 as n, count(rev_user) from huwiki.revision where rev_user >= 1       and rev_user < 10000
union select  100000 as n, count(rev_user) from huwiki.revision where rev_user >= 10000   and rev_user < 100000
union select 1000000 as n, count(rev_user) from huwiki.revision where rev_user >= 100000  and rev_user < 1000000
union select 10000000 as n, count(rev_user) from huwiki.revision where rev_user >= 1000000;

-- results on 2016-03-08:
-- +----------+-----------------+
-- | n        | count(rev_user) |
-- +----------+-----------------+
-- |        1 |          848644 |
-- |    10000 |         3994674 |
-- |   100000 |         6839829 |
-- |  1000000 |         4652542 |
-- | 10000000 |               0 |
-- +----------+-----------------+
-- 5 rows in set (3 min 16.91 sec)

ALTER TABLE huwiki.logging
  DROP PRIMARY KEY,
  ADD PRIMARY KEY (log_id, log_user)
  PARTITION BY RANGE (log_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p10000 VALUES LESS THAN (10000),
  PARTITION p50000 VALUES LESS THAN (50000),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION p1000000 VALUES LESS THAN (1000000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

ALTER TABLE huwiki.revision
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
  PARTITION p10000 VALUES LESS THAN (10000),
  PARTITION p50000 VALUES LESS THAN (50000),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION p1000000 VALUES LESS THAN (1000000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

-- kowiki

      select       1 as n, count(rev_user) from kowiki.revision where rev_user  < 1
union select   10000 as n, count(rev_user) from kowiki.revision where rev_user >= 1       and rev_user < 10000
union select  100000 as n, count(rev_user) from kowiki.revision where rev_user >= 10000   and rev_user < 100000
union select 1000000 as n, count(rev_user) from kowiki.revision where rev_user >= 100000  and rev_user < 1000000
union select 10000000 as n, count(rev_user) from kowiki.revision where rev_user >= 1000000;

-- results on 2016-03-08:
-- +----------+-----------------+
-- | n        | count(rev_user) |
-- +----------+-----------------+
-- |        1 |         2914454 |
-- |    10000 |         2113366 |
-- |   100000 |         5498149 |
-- |  1000000 |         4429860 |
-- | 10000000 |               0 |
-- +----------+-----------------+
-- 5 rows in set (12 min 12.72 sec)

ALTER TABLE kowiki.logging
  DROP PRIMARY KEY,
  ADD PRIMARY KEY (log_id, log_user)
  PARTITION BY RANGE (log_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p10000 VALUES LESS THAN (10000),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION p1000000 VALUES LESS THAN (1000000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

ALTER TABLE kowiki.revision
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
  PARTITION p10000 VALUES LESS THAN (10000),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION p1000000 VALUES LESS THAN (1000000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

-- metawiki

      select       1 as n, count(rev_user) from metawiki.revision where rev_user  < 1
union select  100000 as n, count(rev_user) from metawiki.revision where rev_user >= 1       and rev_user < 100000
union select  500000 as n, count(rev_user) from metawiki.revision where rev_user >= 100000  and rev_user < 500000
union select 1000000 as n, count(rev_user) from metawiki.revision where rev_user >= 500000  and rev_user < 1000000
union select 9000000 as n, count(rev_user) from metawiki.revision where rev_user >= 1000000 and rev_user < 9000000;

-- results on 2016-03-08:
-- +---------+-----------------+
-- | n       | count(rev_user) |
-- +---------+-----------------+
-- |       1 |          300217 |
-- |  100000 |         3652865 |
-- |  500000 |          568446 |
-- | 1000000 |         9101305 |
-- | 9000000 |         1363336 |
-- +---------+-----------------+
-- 5 rows in set (8 min 35.75 sec)

ALTER TABLE metawiki.logging
  DROP PRIMARY KEY,
  ADD PRIMARY KEY (log_id, log_user)
  PARTITION BY RANGE (log_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p10000 VALUES LESS THAN (10000),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION p750000 VALUES LESS THAN (750000),
  PARTITION p1000000 VALUES LESS THAN (1000000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

ALTER TABLE metawiki.revision
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
  PARTITION p10000 VALUES LESS THAN (10000),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION p750000 VALUES LESS THAN (750000),
  PARTITION p1000000 VALUES LESS THAN (1000000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );


-- rowiki

      select       1 as n, count(rev_user) from rowiki.revision where rev_user  < 1
union select   10000 as n, count(rev_user) from rowiki.revision where rev_user >= 1       and rev_user < 10000
union select  100000 as n, count(rev_user) from rowiki.revision where rev_user >= 10000   and rev_user < 100000
union select 1000000 as n, count(rev_user) from rowiki.revision where rev_user >= 100000  and rev_user < 1000000
union select 2000000 as n, count(rev_user) from rowiki.revision where rev_user >= 1000000;

-- results on 2016-03-08:
-- +---------+-----------------+
-- | n       | count(rev_user) |
-- +---------+-----------------+
-- |       1 |          554495 |
-- |   10000 |         1878970 |
-- |  100000 |         4406690 |
-- | 1000000 |         2989038 |
-- | 2000000 |               0 |
-- +---------+-----------------+
-- 5 rows in set (11 min 50.74 sec)

ALTER TABLE rowiki.logging
  DROP PRIMARY KEY,
  ADD PRIMARY KEY (log_id, log_user)
  PARTITION BY RANGE (log_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p10000 VALUES LESS THAN (10000),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION p1000000 VALUES LESS THAN (1000000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

ALTER TABLE rowiki.revision
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
  PARTITION p10000 VALUES LESS THAN (10000),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION p1000000 VALUES LESS THAN (1000000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

-- ukwiki

      select       1 as n, count(rev_user) from ukwiki.revision where rev_user  < 1
union select   10000 as n, count(rev_user) from ukwiki.revision where rev_user >= 1       and rev_user < 10000
union select  100000 as n, count(rev_user) from ukwiki.revision where rev_user >= 10000   and rev_user < 100000
union select 1000000 as n, count(rev_user) from ukwiki.revision where rev_user >= 100000  and rev_user < 1000000
union select 2000000 as n, count(rev_user) from ukwiki.revision where rev_user >= 1000000;

-- results on 2016-03-08:
-- +---------+-----------------+
-- | n       | count(rev_user) |
-- +---------+-----------------+
-- |       1 |         1025084 |
-- |   10000 |         4420539 |
-- |  100000 |         8301343 |
-- | 1000000 |         3202266 |
-- | 2000000 |               0 |
-- +---------+-----------------+
-- 5 rows in set (19 min 58.35 sec)

ALTER TABLE ukwiki.logging
  DROP PRIMARY KEY,
  ADD PRIMARY KEY (log_id, log_user)
  PARTITION BY RANGE (log_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p10000 VALUES LESS THAN (10000),
  PARTITION p50000 VALUES LESS THAN (50000),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION p1000000 VALUES LESS THAN (1000000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

ALTER TABLE ukwiki.revision
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
  PARTITION p10000 VALUES LESS THAN (10000),
  PARTITION p50000 VALUES LESS THAN (50000),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION p1000000 VALUES LESS THAN (1000000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

-- viwiki

      select       1 as n, count(rev_user) from viwiki.revision where rev_user  < 1
union select  100000 as n, count(rev_user) from viwiki.revision where rev_user >= 1       and rev_user < 100000
union select  200000 as n, count(rev_user) from viwiki.revision where rev_user >= 100000  and rev_user < 200000
union select  300000 as n, count(rev_user) from viwiki.revision where rev_user >= 200000  and rev_user < 300000
union select 1000000 as n, count(rev_user) from viwiki.revision where rev_user >= 300000  and rev_user < 1000000;

-- results on 2016-03-08:
-- +---------+-----------------+
-- | n       | count(rev_user) |
-- +---------+-----------------+
-- |       1 |          873978 |
-- |  100000 |         5081899 |
-- |  200000 |         3295187 |
-- |  300000 |         7851401 |
-- | 1000000 |         5586354 |
-- +---------+-----------------+
-- 5 rows in set (29 min 14.88 sec)

ALTER TABLE viwiki.logging
  DROP PRIMARY KEY,
  ADD PRIMARY KEY (log_id, log_user)
  PARTITION BY RANGE (log_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p10000 VALUES LESS THAN (10000),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION p200000 VALUES LESS THAN (200000),
  PARTITION p250000 VALUES LESS THAN (250000),
  PARTITION p300000 VALUES LESS THAN (300000),
  PARTITION p400000 VALUES LESS THAN (400000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

ALTER TABLE viwiki.revision
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
  PARTITION p10000 VALUES LESS THAN (10000),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION p200000 VALUES LESS THAN (200000),
  PARTITION p250000 VALUES LESS THAN (250000),
  PARTITION p300000 VALUES LESS THAN (300000),
  PARTITION p400000 VALUES LESS THAN (400000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );
