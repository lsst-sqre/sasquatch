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

echo "Uploading backup to Google Cloud Storage..."
gsutil cp -r "$BACKUP_PATH" "$GCS_BUCKET"

if [ $? -eq 0 ]; then
    echo "Backup uploaded successfully to $GCS_BUCKET."
else
    echo "Failed to upload backup to GCS!" >&2
    exit 1
fi
