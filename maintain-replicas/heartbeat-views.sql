-- TODO: add it to maintain-replicas
-- This only has to be run once per host
-- And there is no checks that the underlying tables exist
CREATE DATABASE IF NOT EXISTS `heartbeat_p`;
CREATE
ALGORITHM=UNDEFINED
DEFINER=`root`@`localhost`
SQL SECURITY DEFINER VIEW
`heartbeat_p`.`heartbeat` AS
SELECT (
CASE
WHEN (`heartbeat`.`heartbeat`.`file` like 'db1052%') THEN 's1'
WHEN (`heartbeat`.`heartbeat`.`file` like 'db1024%') THEN 's2'
WHEN (`heartbeat`.`heartbeat`.`file` like 'db1038%') THEN 's3'
WHEN (`heartbeat`.`heartbeat`.`file` like 'db1040%') THEN 's4'
WHEN (`heartbeat`.`heartbeat`.`file` like 'db1058%') THEN 's5'
WHEN (`heartbeat`.`heartbeat`.`file` like 'db1023%') THEN 's6'
WHEN (`heartbeat`.`heartbeat`.`file` like 'db1033%') THEN 's7'
ELSE 'unknown' end
) AS `shard`,
`heartbeat`.`heartbeat`.`ts` AS `last_updated`,
timestampdiff(SECOND,`heartbeat`.`heartbeat`.`ts`,utc_timestamp()) AS `lag`
FROM `heartbeat`.`heartbeat`;
-- Change SECOND precission to MICROSECOND when this bug disappears:
-- https://mariadb.atlassian.net/browse/MDEV-9175
