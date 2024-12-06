#!/bin/bash

# Loop to create tables pc000 to pc255
for i in $(seq -w 0 255); do
    TABLE_NAME="pc$i"
    SQL="set session sql_log_bin=0;CREATE TABLE \`$TABLE_NAME\` (
      \`keyname\` varbinary(255) NOT NULL DEFAULT '',
      \`value\` mediumblob DEFAULT NULL,
      \`exptime\` datetime DEFAULT NULL,
      UNIQUE KEY \`keyname\` (\`keyname\`),
      KEY \`exptime\` (\`exptime\`)
    ) ENGINE=InnoDB DEFAULT CHARSET=binary;"

    # Execute SQL command
    echo "Creating table $TABLE_NAME..."
    mysql parsercache -e "$SQL"
    if [ $? -eq 0 ]; then
        echo "Table $TABLE_NAME created successfully."
    else
        echo "Failed to create table $TABLE_NAME."
    fi
done

echo "All tables processed."
