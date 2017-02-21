-- frwiki

      select       1 as n, count(rev_user) from frwiki.revision where rev_user  < 1
union select   10000 as n, count(rev_user) from frwiki.revision where rev_user >= 1       and rev_user <  10000
union select   20000 as n, count(rev_user) from frwiki.revision where rev_user >= 10000   and rev_user <  20000
union select   30000 as n, count(rev_user) from frwiki.revision where rev_user >= 20000   and rev_user <  30000
union select   40000 as n, count(rev_user) from frwiki.revision where rev_user >= 30000   and rev_user <  40000
union select   50000 as n, count(rev_user) from frwiki.revision where rev_user >= 40000   and rev_user <  50000
union select  100000 as n, count(rev_user) from frwiki.revision where rev_user >= 50000   and rev_user < 100000
union select  200000 as n, count(rev_user) from frwiki.revision where rev_user >= 100000  and rev_user < 200000
union select  300000 as n, count(rev_user) from frwiki.revision where rev_user >= 200000  and rev_user < 300000
union select  400000 as n, count(rev_user) from frwiki.revision where rev_user >= 300000  and rev_user < 400000
union select  500000 as n, count(rev_user) from frwiki.revision where rev_user >= 400000  and rev_user < 500000
union select 1000000 as n, count(rev_user) from frwiki.revision where rev_user >= 500000  and rev_user < 1000000
union select 2000000 as n, count(rev_user) from frwiki.revision where rev_user >= 1000000 and rev_user < 2000000
union select 3000000 as n, count(rev_user) from frwiki.revision where rev_user >= 2000000;

-- results on 2016-03-07:
-- +---------+-----------------+
-- | n       | count(rev_user) |
-- +---------+-----------------+
-- |       1 |        15638394 |
-- |   10000 |         6914711 |
-- |   20000 |         3372557 |
-- |   30000 |         4133218 |
-- |   40000 |         3820140 |
-- |   50000 |         3235927 |
-- |  100000 |         8347306 |
-- |  200000 |        16201008 |
-- |  300000 |        10825620 |
-- |  400000 |         9228063 |
-- |  500000 |         5028945 |
-- | 1000000 |        15686998 |
-- | 2000000 |        13874767 |
-- | 3000000 |         1572649 |
-- +---------+-----------------+
-- 14 rows in set (5 min 52.62 sec)

ALTER TABLE frwiki.logging
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
  PARTITION p125000 VALUES LESS THAN (125000),
  PARTITION p150000 VALUES LESS THAN (150000),
  PARTITION p175000 VALUES LESS THAN (175000),
  PARTITION p200000 VALUES LESS THAN (200000),
  PARTITION p250000 VALUES LESS THAN (250000),
  PARTITION p300000 VALUES LESS THAN (300000),
  PARTITION p400000 VALUES LESS THAN (400000),
  PARTITION p500000 VALUES LESS THAN (500000),
  PARTITION p600000 VALUES LESS THAN (600000),
  PARTITION p700000 VALUES LESS THAN (700000),
  PARTITION p800000 VALUES LESS THAN (800000),
  PARTITION p900000 VALUES LESS THAN (900000),
  PARTITION p1000000 VALUES LESS THAN (1000000),
  PARTITION p1500000 VALUES LESS THAN (1500000),
  PARTITION p2000000 VALUES LESS THAN (2000000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

ALTER TABLE frwiki.revision
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
  PARTITION p20000 VALUES LESS THAN (20000),
  PARTITION p30000 VALUES LESS THAN (30000),
  PARTITION p40000 VALUES LESS THAN (40000),
  PARTITION p50000 VALUES LESS THAN (50000),
  PARTITION p75000 VALUES LESS THAN (75000),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION p125000 VALUES LESS THAN (125000),
  PARTITION p150000 VALUES LESS THAN (150000),
  PARTITION p175000 VALUES LESS THAN (175000),
  PARTITION p200000 VALUES LESS THAN (200000),
  PARTITION p250000 VALUES LESS THAN (250000),
  PARTITION p300000 VALUES LESS THAN (300000),
  PARTITION p400000 VALUES LESS THAN (400000),
  PARTITION p500000 VALUES LESS THAN (500000),
  PARTITION p600000 VALUES LESS THAN (600000),
  PARTITION p700000 VALUES LESS THAN (700000),
  PARTITION p800000 VALUES LESS THAN (800000),
  PARTITION p900000 VALUES LESS THAN (900000),
  PARTITION p1000000 VALUES LESS THAN (1000000),
  PARTITION p1500000 VALUES LESS THAN (1500000),
  PARTITION p2000000 VALUES LESS THAN (2000000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

-- ruwiki

      select       1 as n, count(rev_user) from ruwiki.revision where rev_user  < 1
union select   10000 as n, count(rev_user) from ruwiki.revision where rev_user >= 1       and rev_user <  10000
union select   20000 as n, count(rev_user) from ruwiki.revision where rev_user >= 10000   and rev_user <  20000
union select   30000 as n, count(rev_user) from ruwiki.revision where rev_user >= 20000   and rev_user <  30000
union select   40000 as n, count(rev_user) from ruwiki.revision where rev_user >= 30000   and rev_user <  40000
union select   50000 as n, count(rev_user) from ruwiki.revision where rev_user >= 40000   and rev_user <  50000
union select  100000 as n, count(rev_user) from ruwiki.revision where rev_user >= 50000   and rev_user < 100000
union select  200000 as n, count(rev_user) from ruwiki.revision where rev_user >= 100000  and rev_user < 200000
union select  300000 as n, count(rev_user) from ruwiki.revision where rev_user >= 200000  and rev_user < 300000
union select  400000 as n, count(rev_user) from ruwiki.revision where rev_user >= 300000  and rev_user < 400000
union select  500000 as n, count(rev_user) from ruwiki.revision where rev_user >= 400000  and rev_user < 500000
union select 1000000 as n, count(rev_user) from ruwiki.revision where rev_user >= 500000  and rev_user < 1000000
union select 2000000 as n, count(rev_user) from ruwiki.revision where rev_user >= 1000000 and rev_user < 2000000
union select 3000000 as n, count(rev_user) from ruwiki.revision where rev_user >= 2000000;

-- +---------+-----------------+
-- | n       | count(rev_user) |
-- +---------+-----------------+
-- |       1 |        12135172 |
-- |   10000 |         5248819 |
-- |   20000 |         2733849 |
-- |   30000 |         2094022 |
-- |   40000 |         2200810 |
-- |   50000 |         1985636 |
-- |  100000 |         5583611 |
-- |  200000 |         8486887 |
-- |  300000 |         4889031 |
-- |  400000 |         4751174 |
-- |  500000 |         3384289 |
-- | 1000000 |        12957853 |
-- | 2000000 |         4237809 |
-- | 3000000 |               0 |
-- +---------+-----------------+
-- 14 rows in set (3 min 35.96 sec)

ALTER TABLE ruwiki.logging
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
  PARTITION p300000 VALUES LESS THAN (300000),
  PARTITION p400000 VALUES LESS THAN (400000),
  PARTITION p500000 VALUES LESS THAN (500000),
  PARTITION p600000 VALUES LESS THAN (600000),
  PARTITION p750000 VALUES LESS THAN (750000),
  PARTITION p1000000 VALUES LESS THAN (1000000),
  PARTITION p2000000 VALUES LESS THAN (2000000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

ALTER TABLE ruwiki.revision
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
  PARTITION p600000 VALUES LESS THAN (600000),
  PARTITION p750000 VALUES LESS THAN (750000),
  PARTITION p1000000 VALUES LESS THAN (1000000),
  PARTITION p2000000 VALUES LESS THAN (2000000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );


-- jawiki

      select       1 as n, count(rev_user) from jawiki.revision where rev_user  < 1
union select   10000 as n, count(rev_user) from jawiki.revision where rev_user >= 1       and rev_user <  10000
union select   20000 as n, count(rev_user) from jawiki.revision where rev_user >= 10000   and rev_user <  20000
union select   30000 as n, count(rev_user) from jawiki.revision where rev_user >= 20000   and rev_user <  30000
union select   40000 as n, count(rev_user) from jawiki.revision where rev_user >= 30000   and rev_user <  40000
union select   50000 as n, count(rev_user) from jawiki.revision where rev_user >= 40000   and rev_user <  50000
union select  100000 as n, count(rev_user) from jawiki.revision where rev_user >= 50000   and rev_user < 100000
union select  200000 as n, count(rev_user) from jawiki.revision where rev_user >= 100000  and rev_user < 200000
union select  300000 as n, count(rev_user) from jawiki.revision where rev_user >= 200000  and rev_user < 300000
union select  400000 as n, count(rev_user) from jawiki.revision where rev_user >= 300000  and rev_user < 400000
union select  500000 as n, count(rev_user) from jawiki.revision where rev_user >= 400000  and rev_user < 500000
union select 1000000 as n, count(rev_user) from jawiki.revision where rev_user >= 500000  and rev_user < 1000000
union select 2000000 as n, count(rev_user) from jawiki.revision where rev_user >= 1000000;

-- results on 2016-03-07:
-- +---------+-----------------+
-- | n       | count(rev_user) |
-- +---------+-----------------+
-- |       1 |        18757874 |
-- |   10000 |         2444970 |
-- |   20000 |         2238066 |
-- |   30000 |         1604146 |
-- |   40000 |         1682537 |
-- |   50000 |         1195892 |
-- |  100000 |         4615865 |
-- |  200000 |         7725097 |
-- |  300000 |         4367828 |
-- |  400000 |         3440772 |
-- |  500000 |         2256746 |
-- | 1000000 |         5891921 |
-- | 2000000 |          274100 |
-- +---------+-----------------+
-- 13 rows in set (3 min 27.18 sec)

ALTER TABLE jawiki.logging
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
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

ALTER TABLE jawiki.revision
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
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );
