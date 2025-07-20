ARG BUILD_FROM
FROM $BUILD_FROM

# Set shell
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Install Python and required packages
RUN apk add --no-cache \
    python3 \
    py3-pip \
    && pip3 install --no-cache-dir \
        paho-mqtt==1.6.1

# Copy data
COPY run.sh /
COPY rs485_mqtt_ha_proxy.py /app/

# Make script executable
RUN chmod a+x /run.sh

# Set working directory
WORKDIR /app

# Start script
CMD ["/run.sh"]
