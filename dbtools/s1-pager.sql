-- enwiki

      select        1 as n, count(rev_user) from enwiki.revision where rev_user  <        1
union select    50000 as n, count(rev_user) from enwiki.revision where rev_user >=        1 and rev_user <    50000
union select   100000 as n, count(rev_user) from enwiki.revision where rev_user >=    50000 and rev_user <   100000
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
union select 20000000 as n, count(rev_user) from enwiki.revision where rev_user >= 18000000 and rev_user < 20000000
union select 22000000 as n, count(rev_user) from enwiki.revision where rev_user >= 20000000 and rev_user < 22000000
union select 24000000 as n, count(rev_user) from enwiki.revision where rev_user >= 22000000 and rev_user < 24000000
union select 99999999 as n, count(rev_user) from enwiki.revision where rev_user >= 24000000;

--
-- Results on 2015-12-29:
--
-- +----------+-----------------+
-- | n        | count(rev_user) |
-- +----------+-----------------+
-- |        1 |       143012851 |
-- |    50000 |        22262399 |
-- |   100000 |        17246412 |
-- |   200000 |        23860120 |
-- |   300000 |        22837407 |
-- |   400000 |        14815911 |
-- |   500000 |        13818622 |
-- |   750000 |        23865783 |
-- |  1000000 |        17747080 |
-- |  1500000 |        32002927 |
-- |  2000000 |        26416371 |
-- |  3000000 |        26939492 |
-- |  4000000 |        29456398 |
-- |  5000000 |        25721791 |
-- |  6000000 |        19401515 |
-- |  7000000 |        20810745 |
-- |  8000000 |        26390816 |
-- |  9000000 |        13651989 |
-- | 10000000 |        12830219 |
-- | 12000000 |        25810888 |
-- | 14000000 |        24018280 |
-- | 16000000 |        17205483 |
-- | 18000000 |        15013314 |
-- | 20000000 |        10100942 |
-- | 22000000 |         9036396 |
-- | 24000000 |         3941295 |
-- | 99999999 |         5808754 |
-- +----------+-----------------+
-- 27 rows in set (3 hours 27 min 43.58 sec)

ALTER TABLE enwiki.logging
  DROP PRIMARY KEY,
  ADD PRIMARY KEY (log_id, log_user)
  PARTITION BY RANGE (log_user) (
  PARTITION p1 VALUES LESS THAN (1),
  PARTITION p50000 VALUES LESS THAN (50000),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION p200000 VALUES LESS THAN (200000),
  PARTITION p300000 VALUES LESS THAN (300000),
  PARTITION p400000 VALUES LESS THAN (400000),
  PARTITION p500000 VALUES LESS THAN (500000),
  PARTITION p750000 VALUES LESS THAN (750000),
  PARTITION p1000000 VALUES LESS THAN (1000000),
  PARTITION p1250000 VALUES LESS THAN (1250000),
  PARTITION p1500000 VALUES LESS THAN (1500000),
  PARTITION p1750000 VALUES LESS THAN (1750000),
  PARTITION p2000000 VALUES LESS THAN (2000000),
  PARTITION p2500000 VALUES LESS THAN (2500000),
  PARTITION p3000000 VALUES LESS THAN (3000000),
  PARTITION p3500000 VALUES LESS THAN (3500000),
  PARTITION p4000000 VALUES LESS THAN (4000000),
  PARTITION p4500000 VALUES LESS THAN (4500000),
  PARTITION p5000000 VALUES LESS THAN (5000000),
  PARTITION p6000000 VALUES LESS THAN (6000000),
  PARTITION p7000000 VALUES LESS THAN (7000000),
  PARTITION p7500000 VALUES LESS THAN (7500000),
  PARTITION p8000000 VALUES LESS THAN (8000000),
  PARTITION p9000000 VALUES LESS THAN (9000000),
  PARTITION p10000000 VALUES LESS THAN (10000000),
  PARTITION p11000000 VALUES LESS THAN (11000000),
  PARTITION p12000000 VALUES LESS THAN (12000000),
  PARTITION p13000000 VALUES LESS THAN (13000000),
  PARTITION p14000000 VALUES LESS THAN (14000000),
  PARTITION p16000000 VALUES LESS THAN (16000000),
  PARTITION p18000000 VALUES LESS THAN (18000000),
  PARTITION p22000000 VALUES LESS THAN (22000000),
  PARTITION p24000000 VALUES LESS THAN (24000000),
  PARTITION p28000000 VALUES LESS THAN (28000000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

ALTER TABLE enwiki.revision
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
  PARTITION p50000 VALUES LESS THAN (50000),
  PARTITION p100000 VALUES LESS THAN (100000),
  PARTITION p200000 VALUES LESS THAN (200000),
  PARTITION p300000 VALUES LESS THAN (300000),
  PARTITION p400000 VALUES LESS THAN (400000),
  PARTITION p500000 VALUES LESS THAN (500000),
  PARTITION p750000 VALUES LESS THAN (750000),
  PARTITION p1000000 VALUES LESS THAN (1000000),
  PARTITION p1250000 VALUES LESS THAN (1250000),
  PARTITION p1500000 VALUES LESS THAN (1500000),
  PARTITION p1750000 VALUES LESS THAN (1750000),
  PARTITION p2000000 VALUES LESS THAN (2000000),
  PARTITION p2500000 VALUES LESS THAN (2500000),
  PARTITION p3000000 VALUES LESS THAN (3000000),
  PARTITION p3500000 VALUES LESS THAN (3500000),
  PARTITION p4000000 VALUES LESS THAN (4000000),
  PARTITION p4500000 VALUES LESS THAN (4500000),
  PARTITION p5000000 VALUES LESS THAN (5000000),
  PARTITION p6000000 VALUES LESS THAN (6000000),
  PARTITION p7000000 VALUES LESS THAN (7000000),
  PARTITION p7500000 VALUES LESS THAN (7500000),
  PARTITION p8000000 VALUES LESS THAN (8000000),
  PARTITION p9000000 VALUES LESS THAN (9000000),
  PARTITION p10000000 VALUES LESS THAN (10000000),
  PARTITION p11000000 VALUES LESS THAN (11000000),
  PARTITION p12000000 VALUES LESS THAN (12000000),
  PARTITION p13000000 VALUES LESS THAN (13000000),
  PARTITION p14000000 VALUES LESS THAN (14000000),
  PARTITION p16000000 VALUES LESS THAN (16000000),
  PARTITION p18000000 VALUES LESS THAN (18000000),
  PARTITION p22000000 VALUES LESS THAN (22000000),
  PARTITION p24000000 VALUES LESS THAN (24000000),
  PARTITION p28000000 VALUES LESS THAN (28000000),
  PARTITION pMAXVALUE VALUES LESS THAN MAXVALUE );

