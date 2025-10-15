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

  backup_dir="/backup/sasquatch-influxdb-enterprise-incremental"
  backup_logs="$backup_dir/backup-$(get_timestamp).logs"
  mkdir -p "$backup_dir"

  if ! influxd-ctl -bind $bind:8091 backup -strategy incremental "$backup_dir" > "$backup_logs" 2>&1; then
    echo "InfluxDB Enterprise backup failed. See logs at $backup_logs"
    return 1
  fi

  echo "Backup completed successfully at $backup_dir. Logs stored at $backup_logs."
}

get_last_completed_shard_id() {
  local bind="$1"
  local db="$2"
  if [ -z "$bind" ]; then
    echo "Error: bind address is required to retrieve shard ID."
    return 1
  fi

  local now="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

  # Look for the shard with EndTime ≤ now
  local shard= $(influxd-ctl -bind meta:8091 show-shards | awk -v db=$db -v now=$now '
  /^[[:space:]]*ID[[:space:]]/ {seen=1; next} seen && $2==$db && $7 <= now {print $1, $7}
  ' | sort -k2,2 | tail -n1 )

  if [ -z "$shard" ]; then
    echo "Error: could not retrieve shard ID from InfluxDB Enterprise."
    return 1
  fi

  local shard_id=$(echo "$shard" | awk '{print $1}')
  local end_time=$(echo "$shard" | awk '{print $2}')

  echo "Last completed shard ID: $shard_id with EndTime: $end_time"

  echo "$shard_id"
}

backup_influxdb_enterprise_shard() {
  # Required from BACKUP_ITEMS:
  #   bind:         InfluxDB Enterprise meta service address without port
  #   gcsBucket:    e.g. "gs://my-backup-bucket"
  # Optional:
  #   gcsPrefix:    e.g. "sasquatch/influxdb/shards"
  #   db:           limit to a single database
  #   retentionDays: remove backups older than the specified number of days

  local shard_id="$(get_last_completed_shard_id $bind $db)"
  echo "Backing up shard $shard_id from InfluxDB Enterprise..."

  if [ -z "$bind" ]; then
    echo "Missing 'bind' for InfluxDB Enterprise."
    return 1
  fi
  if [ -z "$gcsBucket" ]; then
    echo "Missing 'gcsBucket' (e.g., gs://my-bucket)."
    return 1
  fi

  local ts="$(get_timestamp)"
  local base_dir="/backup/influxdb-enterprise-shard-${shard_id}"
  mkdir -p "$base_dir"
  local backup_logs="$base_dir/backup-${ts}.log"

  # Perform shard backups
  local backup_dir="$base_dir/data"
  mkdir -p "$backup_dir"

  # TODO: confirm if manifest for single-shard backup is created automatically and has the shard start and end times

  if ! influxd-ctl -bind "$bind:8091" backup -shard "$sid" "$backup_dir" >> "$backup_logs" 2>&1; then
    echo "Backup failed for shard $sid. See $backup_logs"
    return 1
  fi

  # Write checksum manifest for all files produced
  echo "Generating SHA256 checksums..."
  (cd "$backup_dir" && find . -type f -print0 | xargs -0 sha256sum) > "$base_dir/SHA256SUMS.txt" || {
    echo "Failed to generate checksum manifest."
    return 1
  }

  # Compose GCS destination: bucket/prefix/<timestamp>/
  if [ -n "$gcsPrefix" ]; then
    dest_uri="${gcsBucket%/}/$gcsPrefix/influxdb-enterprise-shard-${shard_id}/"
  else
    dest_uri="${gcsBucket%/}/influxdb-enterprise-shard-${shard_id}/"
  fi

  echo "Uploading to $dest_uri ..."
  # gsutil cp validates integrity with checksums on upload
  if ! gsutil -m cp -r "$backup_dir" "$base_dir/SHA256SUMS.txt" "$dest_uri" >> "$backup_logs" 2>&1; then
    echo "Upload to GCS failed. See $backup_logs"
    return 1
  fi

  # If we made it here, copies were checksum-validated.
  echo "Upload complete. Removing local backup at $base_dir ..."
  rm -rf "$base_dir" || echo "Warning: failed to remove $base_dir"

  echo "Shard backup completed successfully."
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
  retention_days=$(echo "$item" | jq -r '.retentionDays // empty')
  bind=$(echo "$item" | jq -r '.bind // empty')

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
