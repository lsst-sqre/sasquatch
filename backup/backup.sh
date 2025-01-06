#!/bin/bash

set -e

backup_chronograf() {
  echo "Backing up Chronograf..."
  pod=$(kubectl get pods -n sasquatch -l app=sasquatch-chronograf -o jsonpath='{.items[0].metadata.name}')
  backup_dir="/backup/chronograf-$(date +%Y-%m-%d)"
  mkdir -p "$backup_dir"
  kubectl cp -n sasquatch "$pod:/var/lib/chronograf/chronograf-v1.db" "$backup_dir/chronograf-v1.db" > /dev/null 2>&1
  if [ $? -eq 0 ] && [ -f "$backup_dir/chronograf-v1.db" ]; then
    echo "Backup completed successfully at $backup_dir."
    echo "Cleaning up backups older than $retention_days day(s)..."
    find /backup -type d -name "chronograf-*" -mtime +$retention_days -exec rm -rf {} \;
  else
    echo "Backup failed!" >&2
    exit 1
  fi
}

backup_kapacitor() {
  echo "Backing up Kapacitor..."
  pod=$(kubectl get pods -n sasquatch -l app=sasquatch-kapacitor -o jsonpath='{.items[0].metadata.name}')
  backup_dir="/backup/kapacitor-$(date +%Y-%m-%d)"
  mkdir -p "$backup_dir"
  kubectl cp -n sasquatch "$pod:/var/lib/kapacitor/kapacitor.db" "$backup_dir/kapacitor.db" > /dev/null 2>&1
  if [ $? -eq 0 ] && [ -f "$backup_dir/kapacitor.db" ]; then
    echo "Backup completed successfully at $backup_dir."
    echo "Cleaning up backups older than $retention_days day(s)..."
    find /backup -type d -name "kapacitor-*" -mtime +$retention_days -exec rm -rf {} \;
  else
    echo "Backup failed!" >&2
    exit 1
  fi
}

backup_influxdb_enterprise_incremental() {
  echo "Backing up InfluxDB Enterprise (incremental backup)..."
  backup_dir="/backup/sasquatch-influxdb-enterprise-backup"
  backup_logs="/backup/sasquatch-influxdb-enterprise-backup/backup-$(date +%Y-%m-%d).logs"
  mkdir -p "$backup_dir"
  influxd-ctl -bind sasquatch-influxdb-enterprise-meta.sasquatch:8091 backup -strategy incremental "$backup_dir" > $backup_logs 2>&1
  if [ $? -eq 0 ]; then
    echo "Backup completed successfully at $backup_dir."
  else
    echo "Backup failed!" >&2
    exit 1
  fi
}

if [ -z "$BACKUP_ITEMS" ]; then
  echo "No backup items specified. Exiting."
  exit 0
fi

BACKUP_ITEMS=$(echo "$BACKUP_ITEMS" | jq -c '.[]')

for item in $BACKUP_ITEMS; do
  name=$(echo "$item" | jq -r '.name')
  enabled=$(echo "$item" | jq -r '.enabled')
  retention_days=$(echo "$item" | jq -r '.retention_days')

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
      *)
        echo "Unknown backup item: $name. Skipping..."
        ;;
    esac
  else
    echo "Skipping $name..."
  fi
done
echo "Backup contents:"
ls -lhtR /backup
