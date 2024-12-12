#!/bin/bash

set -e

# Configuration
BACKUP_DIR="/backup/sasquatch-influxdb-enterprise-backup"
GCS_BUCKET="gs://your-gcs-bucket"

# Ensure the backup directory exists
mkdir -p "$BACKUP_DIR"

echo "Starting InfluxDB Enterprise backup..."

influxd-ctl -bind sasquatch-influxdb-enterprise-meta.sasquatch:8091 backup -strategy incremental "$BACKUP_DIR" 

if [ $? -eq 0 ]; then
    echo "Backup completed successfully at $BACKUP_DIR."
else
    echo "Backup failed!" >&2
    exit 1
fi


