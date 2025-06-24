#!/bin/bash

# Function to generate a timestamp in ISO 8601 format without separators
get_timestamp() {
  date -u +"%Y%m%dT%H%M%SZ"
}

backup_chronograf() {
  echo "Backing up Chronograf..."
  pod=$(kubectl get pods -n sasquatch -l app=sasquatch-chronograf -o jsonpath='{.items[0].metadata.name}')
  if [ -z "$pod" ]; then
    echo "Chronograf pod not found."
    return 1
  fi

  backup_dir="/backup/chronograf-$(get_timestamp)"
  mkdir -p "$backup_dir"

  if ! kubectl cp -n sasquatch "$pod:/var/lib/chronograf/chronograf-v1.db" "$backup_dir/chronograf-v1.db"; then
    echo "Failed to copy Chronograf DB."
    return 1
  fi

  echo "Backup completed successfully at $backup_dir."

  echo "Cleaning up backups older than $retention_days day(s)..."
  if ! find /backup -type d -name "chronograf-*" -mtime +$retention_days -exec rm -rf {} \;; then
    echo "Warning: failed to clean up old Chronograf backups."
  fi
}

backup_kapacitor() {
  echo "Backing up Kapacitor..."

  pod=$(kubectl get pods -n sasquatch -l app=sasquatch-kapacitor -o jsonpath='{.items[0].metadata.name}')
  if [ -z "$pod" ]; then
    echo "Kapacitor pod not found."
    return 1
  fi

  backup_dir="/backup/kapacitor-$(get_timestamp)"
  mkdir -p "$backup_dir"

  if ! kubectl cp -n sasquatch "$pod:/var/lib/kapacitor/kapacitor.db" "$backup_dir/kapacitor.db"; then
    echo "Failed to copy Kapacitor DB from pod $pod."
    return 1
  fi

  echo "Backup completed successfully at $backup_dir."

  echo "Cleaning up backups older than $retention_days day(s)..."
  if ! find /backup -type d -name "kapacitor-*" -mtime +$retention_days -exec rm -rf {} \;; then
    echo "Warning: failed to clean up old Kapacitor backups."
  fi
}


backup_influxdb_enterprise_incremental() {
  echo "Backing up InfluxDB Enterprise (incremental backup)..."

  backup_dir="/backup/sasquatch-influxdb-enterprise-backup"
  backup_logs="$backup_dir/backup-$(get_timestamp).logs"
  mkdir -p "$backup_dir"

  if ! influxd-ctl -bind sasquatch-influxdb-enterprise-meta.sasquatch:8091 backup -strategy incremental "$backup_dir" > "$backup_logs" 2>&1; then
    echo "InfluxDB Enterprise backup failed. See logs at $backup_logs"
    return 1
  fi

  echo "Backup completed successfully at $backup_dir. Logs stored at $backup_logs."
}

backup_influxdb_oss_full() {
  echo "Backing up InfluxDB OSS (full backup)..."

  backup_dir="/backup/sasquatch-influxdb-oss-full-$(get_timestamp)"
  backup_logs="$backup_dir/backup.logs"
  mkdir -p "$backup_dir"

  if ! influxd backup -portable -host sasquatch-influxdb.sasquatch:8088 "$backup_dir" > "$backup_logs" 2>&1; then
    echo "InfluxDB OSS full backup failed. See logs at $backup_logs"
    return 1
  fi

  echo "Backup completed successfully at $backup_dir. Logs stored at $backup_logs."

  echo "Cleaning up backups older than $retention_days day(s)..."
  if ! find /backup -type d -name "sasquatch-influxdb-oss-*" -mtime +$retention_days -exec rm -rf {} \;; then
    echo "Warning: failed to clean up old InfluxDB OSS backups"
  fi
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
        backup_chronograf || echo "Chronograf backup failed."
        ;;
      "kapacitor")
        backup_kapacitor || echo "Kapacitor backup failed."
        ;;
      "influxdb-enterprise-incremental")
        backup_influxdb_enterprise_incremental || echo "InfluxDB Enterprise backup failed."
        ;;
      "influxdb-oss-full")
        backup_influxdb_oss_full || echo "InfluxDB OSS backup failed."
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
