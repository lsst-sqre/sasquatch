#!/bin/bash

set -e

if [ -z "$BACKUP_ITEMS" ]; then
    echo "No backup items specified. Exiting."
    exit 0
fi

BACKUP_ITEMS=$(echo "$BACKUP_ITEMS" | jq -c '.[]')

for item in $BACKUP_ITEMS; do
  name=$(echo "$item" | jq -r '.name')
  enabled=$(echo "$item" | jq -r '.enabled')
  case "$name" in
    "chronograf")
      if [ "$enabled" == "true" ]; then
        echo "Backing up Chronograf..."
        pod=$(kubectl get pods -n sasquatch -l app=sasquatch-chronograf -o jsonpath='{.items[0].metadata.name}')
        backup_dir="/backup/chronograf-$(date +%Y-%m-%d)"
        mkdir -p "$backup_dir"
        kubectl cp -n sasquatch $pod:/var/lib/chronograf/chronograf-v1.db "$backup_dir"/chronograf-v1.db
        if [ $? -eq 0 ] && [ -f "$backup_dir/chronograf-v1.db" ]; then
            echo "Backup completed successfully at $backup_dir."
        else
            echo "Backup failed!" >&2
            exit 1
        fi
      else
        echo "Skipping Chronograf..."
      fi
      ;;
    "kapacitor")
      if [ "$enabled" == "true" ]; then
        echo "Backing up Kapacitor..."
        pod=$(kubectl get pods -n sasquatch -l app=sasquatch-kapacitor -o jsonpath='{.items[0].metadata.name}')
        backup_dir="/backup/kapacitor-$(date +%Y-%m-%d)"
        mkdir -p "$backup_dir"
        kubectl cp -n sasquatch $pod:/var/lib/kapacitor/kapacitor.db "$backup_dir"/kapacitor.db
        if [ $? -eq 0 ] && [ -f "$backup_dir/kapacitor.db" ]; then
            echo "Backup completed successfully at $backup_dir."
        else
            echo "Backup failed!" >&2
            exit 1
        fi
      else
        echo "Skipping Kapacitor..."
      fi
      ;;
    "influxdb-enterprise")
      if [ "$enabled" == "true" ]; then
        echo "Backing up InfluxDB Enterprise (incremental backup)..."
        backup_dir="/backup/sasquatch-influxdb-enterprise-backup"
        mkdir -p "$backup_dir"
        influxd-ctl -bind sasquatch-influxdb-enterprise-meta.sasquatch:8091 backup -strategy incremental "$backup_dir" 
        if [ $? -eq 0 ]; then
            echo "Backup completed successfully at $backup_dir."
        else
            echo "Backup failed!" >&2
            exit 1
        fi
      else
        echo "Skipping InfluxDB Enterprise..."
      fi
      ;;
    *)
      echo "Unknown backup item: $name. Skipping..."
      ;;
  esac
done
echo "Backup directory contents:"
ls -lhtR /backup
