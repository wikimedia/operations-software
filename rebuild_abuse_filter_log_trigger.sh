#!/bin/bash
# Usage: ./rebuild_abuse_filter_log_trigger.sh <hostname>:<port>

set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <hostname>:<port>"
  exit 1
fi

HOST="$1"

MYSQL="db-mysql ${HOST}"
QUERY="SELECT DISTINCT trigger_schema FROM information_schema.triggers WHERE trigger_name LIKE 'abuse_filter_log%';"

WIKIS=$($MYSQL -N -e "$QUERY")

if [[ -z "$WIKIS" ]]; then
  echo "No matching schemas found."
  exit 0
fi

for WIKI in $WIKIS; do

  $MYSQL -e "
    STOP SLAVE;
    DROP TRIGGER IF EXISTS ${WIKI}.abuse_filter_log_update;
    DROP TRIGGER IF EXISTS ${WIKI}.abuse_filter_log_insert;
    CREATE DEFINER=\`root\`@\`localhost\` TRIGGER ${WIKI}.abuse_filter_log_insert
      BEFORE INSERT ON ${WIKI}.abuse_filter_log
      FOR EACH ROW SET NEW.afl_ip_hex = '';
    CREATE DEFINER=\`root\`@\`localhost\` TRIGGER ${WIKI}.abuse_filter_log_update
      BEFORE UPDATE ON ${WIKI}.abuse_filter_log
      FOR EACH ROW SET NEW.afl_ip_hex = '';
    START SLAVE;
  "

  echo "Triggers rebuilt for ${WIKI}"
done
