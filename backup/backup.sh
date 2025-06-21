#!/bin/bash

set -e

# Function to generate a timestamp in ISO 8601 format without separators
get_timestamp() {
  date -u +"%Y%m%dT%H%M%SZ"
}

backup_chronograf() {
  echo "Backing up Chronograf..."
  pod=$(kubectl get pods -n sasquatch -l app=sasquatch-chronograf -o jsonpath='{.items[0].metadata.name}')
  backup_dir="/backup/chronograf-$(get_timestamp)"
  mkdir -p "$backup_dir"

  kubectl cp -n sasquatch "$pod:/var/lib/chronograf/chronograf-v1.db" "$backup_dir/chronograf-v1.db" > /dev/null 2>&1
  echo "Backup completed successfully at $backup_dir."

  echo "Cleaning up backups older than $retention_days day(s)..."
  find /backup -type d -name "chronograf-*" -mtime +$retention_days -exec rm -rf {} \;
}

backup_kapacitor() {
  echo "Backing up Kapacitor..."
  pod=$(kubectl get pods -n sasquatch -l app=sasquatch-kapacitor -o jsonpath='{.items[0].metadata.name}')
  backup_dir="/backup/kapacitor-$(get_timestamp)"
  mkdir -p "$backup_dir"

  kubectl cp -n sasquatch "$pod:/var/lib/kapacitor/kapacitor.db" "$backup_dir/kapacitor.db" > /dev/null 2>&1
  echo "Backup completed successfully at $backup_dir."

  echo "Cleaning up backups older than $retention_days day(s)..."
  find /backup -type d -name "kapacitor-*" -mtime +$retention_days -exec rm -rf {} \;
}

backup_influxdb_enterprise_incremental() {
  echo "Backing up InfluxDB Enterprise (incremental backup)..."
  backup_dir="/backup/sasquatch-influxdb-enterprise-backup"
  backup_logs="$backup_dir/backup-$(get_timestamp).logs"
  mkdir -p "$backup_dir"

  influxd-ctl -bind sasquatch-influxdb-enterprise-meta.sasquatch:8091 backup -strategy incremental "$backup_dir" > "$backup_logs" 2>&1
  echo "Backup completed successfully at $backup_dir. Logs stored at $backup_logs."
}

backup_influxdb_oss_full() {
  echo "Backing up InfluxDB OSS (full backup)..."
  backup_dir="/backup/sasquatch-influxdb-oss-full-$(get_timestamp)"
  backup_logs="$backup_dir/backup.logs"
  mkdir -p "$backup_dir"

  influxd backup -portable -host sasquatch-influxdb.sasquatch:8088 "$backup_dir" > "$backup_logs" 2>&1
  echo "Backup completed successfully at $backup_dir. Logs stored at $backup_logs."

  echo "Cleaning up backups older than $retention_days day(s)..."
  find /backup -type d -name "sasquatch-influxdb-oss-*" -mtime +$retention_days -exec rm -rf {} \;
}

backup_schemas() {
  echo "Backing up schemas..."
  backup_dir="/backup/schemas-$(get_timestamp)"
  mkdir -p "$backup_dir"

  SCHEMA_REGISTRY_URL="http://sasquatch-schema-registry.sasquatch:8081"

  # List all subjects
  subjects=$(curl -s "$SCHEMA_REGISTRY_URL/subjects")

  # Iterate through each subject
  for subject in $(echo $subjects | jq -r '.[]'); do
    # Get all versions of the subject
    versions=$(curl -s "$SCHEMA_REGISTRY_URL/subjects/$subject/versions")

    for version in $(echo $versions | jq -r '.[]'); do
      schema=$(curl -s "$SCHEMA_REGISTRY_URL/subjects/$subject/versions/$version")
      echo $schema | jq '.' > "$backup_dir/${subject}_v${version}.json"
    done
  done

  echo "Backup completed. Files saved to $backup_dir."

  echo "Cleaning up backups older than $retention_days day(s)..."
  find /backup -type d -name "schemas-*" -mtime +$retention_days -exec rm -rf {} \;
}

# Check if BACKUP_ITEMS is set
if [ -z "$BACKUP_ITEMS" ]; then
  echo "No backup items specified. Exiting."
  exit 0
fi

# Process backup items
BACKUP_ITEMS=$(echo "$BACKUP_ITEMS" | jq -c '.[]')

for item in $BACKUP_ITEMS; do
  name=$(echo "$item" | jq -r '.name')
  enabled=$(echo "$item" | jq -r '.enabled')
  retention_days=$(echo "$item" | jq -r '.retentionDays')

  if [ "$enabled" == "true" ]; then
    case "$name" in
      "chronograf")
        backup_chronograf
        ;;
      "kapacitor")
        backup_kapacitor
        ;;
      "influxdb-enterprise-incremental")
        backup_influxdb_enterprise_incremental
        ;;
      "influxdb-oss-full")
        backup_influxdb_oss_full
        ;;
      "schemas")
        backup_schemas
        ;;
      *)
        echo "Unknown backup item: $name. Skipping..."
        ;;
    esac
  else
    echo "Skipping $name..."
  fi
done

echo "Backup contents:"
du -sh /backup/*
