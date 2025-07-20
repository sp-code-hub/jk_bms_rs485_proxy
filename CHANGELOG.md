# Changelog

All notable changes to this add-on will be documented in this file.

## [1.0.0] - 2025-07-20

### Added
- Initial release of JK-BMS RS485 MQTT Proxy
- MQTT integration for receiving RS485 data from JK-BMS
- Home Assistant auto-discovery for automatic sensor creation
- Support for multiple JK-BMS units with automatic registration
- Comprehensive battery monitoring including:
  - State of Charge (SOC) and State of Health (SOH)
  - Battery voltage, current, and power
  - Individual cell voltages and resistances
  - Temperature monitoring (MOS + 4 sensors)
  - Balancing status and current
  - Alarm monitoring and reporting
  - Configuration and protection settings
- Real-time data updates
- Configurable MQTT broker settings
- Multi-architecture support (aarch64, amd64, armhf, armv7, i386)
- Comprehensive logging and error handling

### Features
- Automatic BMS device registration in Home Assistant
- Cell-level monitoring for detailed battery analysis
- Safety alarm detection and reporting
- Diagnostic entity category for configuration data
- Robust error handling and connection management
- Environment variable configuration support
