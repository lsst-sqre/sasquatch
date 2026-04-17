# Start from the InfluxDB Enterprise Meta image
# This provides the InfluxDB Enterprise influxd-ctl command
FROM influxdb:1.11.8-meta

# Install pipx and use it to install gsutil which is required for the backup script
# to upload the backup files to Google Cloud Storage
RUN apt-get update && \
    apt-get install -y python3 python3-pip pipx jq && \
    pipx install gsutil && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Add pipx bin directory to PATH
ENV PATH="/root/.local/bin:$PATH"

# Verify gsutil installation
RUN gsutil --version

# Install kubectl
RUN curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" && \
    chmod +x kubectl && \
    mv kubectl /usr/local/bin/

# Install influxd from InfluxDB OSS 1.11.8
RUN mkdir influxdb-1.11.8 && \
    curl -LO "https://download.influxdata.com/influxdb/releases/influxdb-1.11.8-linux-amd64.tar.gz" && \
    tar xf influxdb-1.11.8-linux-amd64.tar.gz -C influxdb-1.11.8 && \
    mv influxdb-1.11.8/influxd /usr/local/bin/ && \
    rm -rf influxdb-1.11.8-linux-amd64.tar.gz

# Verify influxd installation
RUN influxd version

# Add the backup script
COPY backup/backup.sh /usr/local/bin/backup.sh
RUN chmod +x /usr/local/bin/backup.sh

# Create a new user to run the backup script
RUN useradd --create-home sasquatch

# Switch to the non-root user.
USER sasquatch

# Set the default command for the container
CMD ["/usr/local/bin/backup.sh"]
