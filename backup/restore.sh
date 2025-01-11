#!/bin/bash

set -e

# Function to check if the backup directory exists
check_backup_dir() {
  if [ ! -d "$1" ]; then
    echo "Backup directory $1 does not exist. Exiting."
    exit 1
  fi
}

restore_influxdb_oss_full() {
  echo "Restoring InfluxDB OSS from backup..."
  backup_dir="/backup/sasquatch-influxdb-oss-full-$backup_timestamp"

  check_backup_dir "$backup_dir"

  influxd restore -portable -host sasquatch-influxdb.sasquatch:8088 "$backup_dir" 2>&1
  echo "Restore completed successfully."
}

# Check if RESTORE_ITEMS is set
if [ -z "$RESTORE_ITEMS" ]; then
  echo "No restore items specified. Exiting."
  exit 0
fi

RESTORE_ITEMS=$(echo "$RESTORE_ITEMS" | jq -c '.[]')

# Process each restore item
for item in $RESTORE_ITEMS; do
  name=$(echo "$item" | jq -r '.name')
  enabled=$(echo "$item" | jq -r '.enabled')
  backup_timestamp=$(echo "$item" | jq -r '.backupTimestamp')

  if [ "$enabled" == "true" ]; then
    case "$name" in
      "influxdb-oss-full")
        restore_influxdb_oss_full
        ;;
      *)
        echo "Unknown restore item: $name. Skipping..."
        ;;
    esac
  else
    echo "Skipping $name..."
  fi
done
