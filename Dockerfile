# Start from the InfluxDB Enterprise Meta image
# This provides the InfluxDB Enterprise influxd-ctl command
FROM influxdb:1.11.8-meta

# Install pipx and use it to install gsutil which is required for the backup script
# to upload the backup files to Google Cloud Storage
RUN apt-get update && \
    apt-get install -y python3 python3-pip pipx && \
    pipx install gsutil && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
    
# Add pipx bin directory to PATH
ENV PATH="/root/.local/bin:$PATH"

# Verify gsutil installation
RUN gsutil --version

# Add the backup script
COPY backup/backup.sh /usr/local/bin/backup.sh
RUN chmod +x /usr/local/bin/backup.sh

# Create a new user to run the backup script
RUN useradd --create-home sasquatch

# Switch to the non-root user.
USER sasquatch

# Set the default command for the container
CMD ["/usr/local/bin/backup.sh"]
