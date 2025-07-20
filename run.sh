#!/usr/bin/with-contenv bashio
# ==============================================================================
# Start the JK-BMS RS485 MQTT Proxy service
# ==============================================================================

# Declare variables
declare mqtt_broker_host
declare mqtt_broker_port
declare mqtt_username
declare mqtt_password
declare topic_tx
declare topic_values
declare topic_registration
declare log_level

# Get configuration from options
mqtt_broker_host=$(bashio::config 'mqtt_broker_host')
mqtt_broker_port=$(bashio::config 'mqtt_broker_port')
mqtt_username=$(bashio::config 'mqtt_username')
mqtt_password=$(bashio::config 'mqtt_password')
topic_tx=$(bashio::config 'topic_tx')
topic_values=$(bashio::config 'topic_values')
topic_registration=$(bashio::config 'topic_registration')
log_level=$(bashio::config 'log_level')

# Set log level
bashio::log.level "${log_level}"

bashio::log.info "Starting JK-BMS RS485 MQTT Proxy..."
bashio::log.info "MQTT Broker: ${mqtt_broker_host}:${mqtt_broker_port}"
bashio::log.info "TX Topic: ${topic_tx}"
bashio::log.info "Values Topic: ${topic_values}"
bashio::log.info "Registration Topic: ${topic_registration}"

# Export environment variables for the Python script
export MQTT_BROKER_HOST="${mqtt_broker_host}"
export MQTT_BROKER_PORT="${mqtt_broker_port}"
export MQTT_USERNAME="${mqtt_username}"
export MQTT_PASSWORD="${mqtt_password}"
export TOPIC_TX="${topic_tx}"
export TOPIC_VALUES="${topic_values}"
export TOPIC_REGISTRATION="${topic_registration}"
export LOG_LEVEL="${log_level}"

# Start the Python application
cd /app
exec python3 rs485_mqtt_ha_proxy.py
