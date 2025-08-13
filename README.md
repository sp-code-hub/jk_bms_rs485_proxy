# JK-BMS RS485 MQTT Proxy

![Supports aarch64 Architecture][aarch64-shield] ![Supports amd64 Architecture][amd64-shield] ![Supports armhf Architecture][armhf-shield] ![Supports armv7 Architecture][armv7-shield] ![Supports i386 Architecture][i386-shield]

A Home Assistant addon that acts as an MQTT proxy for JK-BMS RS485 data, providing automatic Home Assistant device discovery and real-time battery monitoring.

## Features

- **MQTT Integration**: Connects to your MQTT broker to receive RS485 data from JK-BMS
- **Home Assistant Auto-Discovery**: Automatically creates sensors and binary sensors in Home Assistant
- **Real-time Monitoring**: Live data updates for battery status, cell voltages, temperatures, and more
- **Multi-BMS Support**: Supports multiple JK-BMS units with automatic registration
- **Comprehensive Data**: Monitors SOC, SOH, voltages, currents, temperatures, alarms, and cell-level data

## Installation

1. Add this repository to your Home Assistant supervisor add-on store
2. Install the "JK-BMS RS485 MQTT Proxy" add-on
3. Configure the add-on options (see Configuration section)
4. Start the add-on

## Configuration

### Basic Configuration

```yaml
mqtt_broker_host: "core-mosquitto"
mqtt_broker_port: 1883
mqtt_username: "homeassistant"
mqtt_password: "your_mqtt_password"
topic_tx: "rs485tx/tx"
topic_values: "rs485tx/bms"
topic_registration: "homeassistant"
log_level: "info"
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `mqtt_broker_host` | string | `core-mosquitto` | MQTT broker hostname or IP address |
| `mqtt_broker_port` | int | `1883` | MQTT broker port |
| `mqtt_username` | string | `homeassistant` | MQTT username |
| `mqtt_password` | string | `` | MQTT password |
| `topic_tx` | string | `rs485tx/tx` | Topic to subscribe for RS485 data |
| `topic_values` | string | `rs485tx/bms` | Topic prefix for publishing BMS values |
| `topic_registration` | string | `homeassistant` | Topic prefix for Home Assistant discovery |
| `log_level` | list | `info` | Log level (trace, debug, info, notice, warning, error, fatal) |

## Usage

1. Ensure your JK-BMS is connected via RS485 and publishing data to the configured MQTT topic
2. Start the addon
3. The addon will automatically discover and register BMS devices in Home Assistant
4. Monitor your battery data through the automatically created entities

## Monitored Data

### Main Sensors
- State of Charge (SOC) %
- State of Health (SOH) %
- Battery Voltage (V)
- Battery Current (A)
- Battery Power (W)
- Remaining Capacity (Ah)
- Total Capacity (Ah)
- Cycle Count
- Temperatures (MOS and 4 temperature sensors)

### Cell-Level Data
- Individual cell voltages
- Individual cell resistances
- Average cell voltage
- Cell voltage difference
- Min/Max cell indices

### Balancing Information
- Balancing current
- Balancing enabled status
- Balancing mode

### Safety & Alarms
- Comprehensive alarm monitoring
- Over/Under voltage protection status
- Temperature protection status
- Current protection status

### Configuration Data (Diagnostic)
- Charge/discharge voltage limits
- Current limits
- Protection thresholds
- Balance settings

## Troubleshooting

### No Data Received
- Check MQTT broker connection
- Verify topic configuration matches your RS485 publisher
- Check RS485 connection to JK-BMS

### Entities Not Appearing
- Ensure Home Assistant MQTT integration is enabled
- Check MQTT discovery topic configuration
- Restart Home Assistant if needed

### Connection Issues
- Verify MQTT broker credentials
- Check network connectivity
- Review addon logs for error messages

## Support

For issues and feature requests, please check the addon logs first and then report issues with detailed information about your setup.

## Changelog

### 1.0.4
- Added MQTT publish result verification with automatic reconnection
- Enhanced safe_publish() method to check message delivery
- Improved reliability for data transmission to Home Assistant
- Better detection of connection issues during publish operations

### 1.0.3
- Added MQTT reconnection on disconnect (5 retry attempts)
- Initial connection retry logic with automatic process exit on failure
- Improved network resilience and error handling

### 1.0.2
- Enhanced logging system with custom timestamp format
- Added configurable log levels (trace, debug, info, warning, error, fatal)
- Improved addon log integration for Home Assistant

### 1.0.1
- Fixed image configuration for Home Assistant addon validation
- Updated addon configuration schema
- Repository structure improvements

### 1.0.0
- Initial release
- Support for JK-BMS RS485 data parsing
- Home Assistant auto-discovery
- Multi-BMS support
- Comprehensive monitoring capabilities

[aarch64-shield]: https://img.shields.io/badge/aarch64-yes-green.svg
[amd64-shield]: https://img.shields.io/badge/amd64-yes-green.svg
[armhf-shield]: https://img.shields.io/badge/armhf-yes-green.svg
[armv7-shield]: https://img.shields.io/badge/armv7-yes-green.svg
[i386-shield]: https://img.shields.io/badge/i386-yes-green.svg
