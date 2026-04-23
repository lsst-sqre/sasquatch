# Backup image

This directory contains the Docker image used for Sasquatch backup and restore
operations.

The image built from `backup/Dockerfile` is separate from the main application
image built from the repository-root `Dockerfile`.

Use the root image for the FastAPI service.
Use the backup image for Kubernetes CronJobs and restore Jobs that require
`kubectl`, `jq`, `influxd`, or `influxd-ctl`.

Build locally with:

```sh
make docker-build-backup
```
