#!/usr/bin/env python3
"""
RS485 MQTT Client for JK-BMS Data
Connects to MQTT broker and displays received binary data in formatted output
https://github.com/txubelaxu/esphome-jk-bms/blob/main/components/jk_rs485_bms/README.md
https://github.com/txubelaxu/esphome-jk-bms/blob/main/components/jk_rs485_sniffer/jk_rs485_sniffer.cpp
https://github.com/txubelaxu/esphome-jk-bms/blob/main/components/jk_rs485_bms/jk_rs485_bms.cpp
"""

import datetime
import json
import logging
import math
import paho.mqtt.client as mqtt
import os
import sys
import time

# Configure logging for Home Assistant addon
def setup_logging(log_level="INFO"):
    """Setup logging configuration for Home Assistant addon."""
    # Convert string log level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create simple formatter without timestamp (we'll add custom timestamps)
    formatter = logging.Formatter(
        fmt='%(message)s'
    )
    
    # Setup root logger
    logger = logging.getLogger()
    logger.setLevel(numeric_level)
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create console handler for addon logs
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

def get_timestamp():
    """Get formatted timestamp in the format: [dd MMM, yyyy, hh:mm:ss.ffffff]"""
    now = datetime.datetime.now()
    return now.strftime("[%d %b, %Y, %H:%M:%S.%f]")
    
class RS485MQTTClient:
    def __init__(self, broker_host, broker_port, username, password, topic_tx, topic_registration, topic_values, log_file="dump.txt"):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.username = username
        self.password = password
        self.topic_tx = topic_tx
        self.topic_registration = topic_registration
        self.topic_values = topic_values
        self.log_file = log_file
        self.client = None
        self.bms_registry = dict()
        self.logger = logging.getLogger(__name__)
        
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.logger.info(f"{get_timestamp()} Connected successfully to MQTT broker at {self.broker_host}:{self.broker_port}")
            client.subscribe(self.topic_tx)
            self.logger.info(f"{get_timestamp()} Subscribed to topic: {self.topic_tx}")
        else:
            self.logger.error(f"{get_timestamp()} Failed to connect to MQTT broker. Return code: {rc}")
            self.print_connection_error(rc)
    
    def on_disconnect(self, client, userdata, rc):
        if rc != 0:
            self.logger.warning(f"{get_timestamp()} Unexpected disconnection from MQTT broker")
            self.simple_reconnect()
        else:
            self.logger.info(f"{get_timestamp()} Disconnected from MQTT broker")
    
    def simple_reconnect(self):
        """Simple reconnect with basic retry logic."""
        for attempt in range(1, 6):  # Try 5 times
            try:
                self.logger.info(f"{get_timestamp()} Reconnect attempt {attempt}/5...")
                time.sleep(5)  # Wait 5 seconds before retry
                self.client.reconnect()
                self.logger.info(f"{get_timestamp()} Reconnected successfully")
                return
            except Exception as e:
                self.logger.error(f"{get_timestamp()} Reconnect attempt {attempt} failed: {e}")
        
        self.logger.error(f"{get_timestamp()} All reconnect attempts failed - exiting process")
        sys.exit(1)
    
    def on_message(self, client, userdata, msg):
        try:
            now = datetime.datetime.now()
            timestamp = now.strftime("[%d %b, %Y, %H:%M:%S.%f]")

            if len(msg.payload) == 319:
                msg.payload = msg.payload[11:]

            if len(msg.payload) == 308 and msg.payload.startswith(b'\x55\xAA\xEB\x90'):                
                # https://github.com/txubelaxu/esphome-jk-bms/blob/main/components/jk_rs485_sniffer/jk_rs485_sniffer.cpp l:812
                # chsumm = msg.payload[299]

                frameType = msg.payload[4]
                frameAddress = 0
                if frameType == 0x01:
                    frameAddress = msg.payload[264 + 6]
                else:
                    frameAddress = msg.payload[300]
                
                truncate = lambda f, n: math.trunc(f * 10**n) / 10**n
                read16 = lambda raw, pos: float(int.from_bytes(raw[pos:pos+2], byteorder='little', signed=True))
                read32 = lambda raw, pos: float(int.from_bytes(raw[pos:pos+4], byteorder='little', signed=True))
                check_bit_of_byte = lambda byte_val, bit_index: (byte_val >> bit_index) & 1

                # Retrieve bms from registry
                bms_registered = frameAddress in self.bms_registry

                if frameType == 0x01: # decode_jk02_settings_

                    if not bms_registered:
                        cellCount = int(read32(msg.payload, 114))
                        self.bms_registry[frameAddress] = cellCount

                        self.logger.info(f"{get_timestamp()} New BMS #{frameAddress} registered ({cellCount} cells)")

                        # main category
                        self.sensor_registration(frameAddress, "SOC", "soc", "battery", "%", None, "state", "{{ value_json.soc | float }}", 1)
                        self.sensor_registration(frameAddress, "SOH", "soh", "battery", "%", None, "state", "{{ value_json.soh | float }}", 1)
                        self.sensor_registration(frameAddress, "Cycles", "cycles", None, None, None, "state", "{{ value_json.cycles | int }}", 0)
                        self.sensor_registration(frameAddress, "Capacity Remaining", "capacity_remaining", None, "Ah", None, "state", "{{ value_json.cap_remaining | float }}", 3)
                        self.sensor_registration(frameAddress, "Capacity Total", "capacity_total", None, "Ah", None, "state", "{{ value_json.cap_total | float }}", 3)
                        self.sensor_registration(frameAddress, "Battery Voltage", "battery_voltage", "voltage", "V", None, "state", "{{ value_json.bat_voltage | float }}", 3)
                        self.sensor_registration(frameAddress, "Battery Current", "battery_current", "current", "A", None, "state", "{{ value_json.bat_current | float }}", 2)
                        self.sensor_registration(frameAddress, "Battery Power", "battery_power", "power", "W", None, "state", "{{ value_json.bat_power | float }}", 2)
                        self.sensor_registration(frameAddress, "Temperature MOS", "temperature_mos", "temperature", "°C", None, "state", "{{ value_json.temp_mos | float }}", 1)
                        self.sensor_registration(frameAddress, "Temperature #1", "temperature_1", "temperature", "°C", None, "state", "{{ value_json.temp1 | float }}", 1)
                        self.sensor_registration(frameAddress, "Temperature #2", "temperature_2", "temperature", "°C", None, "state", "{{ value_json.temp2 | float }}", 1)
                        self.sensor_registration(frameAddress, "Temperature #3", "temperature_3", "temperature", "°C", None, "state", "{{ value_json.temp3 | float }}", 1)
                        self.sensor_registration(frameAddress, "Temperature #4", "temperature_4", "temperature", "°C", None, "state", "{{ value_json.temp4 | float }}", 1)
                        self.sensor_registration(frameAddress, "Cells Average Voltage", "cell_average_voltage", "voltage", "V", None, "state", "{{ value_json.cell_avg_volt | float }}", 3)
                        self.sensor_registration(frameAddress, "Cells Voltage Diff", "cell_voltage_diff", "voltage", "V", None, "state", "{{ value_json.cell_volt_diff | float }}", 3)
                        self.sensor_registration(frameAddress, "Cells Max Index", "cell_max_index", None, None, None, "state", "{{ value_json.cell_max_index | int }}", 0)
                        self.sensor_registration(frameAddress, "Cells Min Index", "cell_min_index", None, None, None, "state", "{{ value_json.cell_min_index | int }}", 0)

                        for i in range(int(cellCount)):
                            self.sensor_registration(
                                frameAddress,
                                f"Cell Voltage #{i+1:02d}",
                                f"cell_voltage_{i+1:02d}",
                                "voltage",
                                "V",
                                None,
                                "state",
                                f"{{{{ value_json.cv{i+1:02d} | float }}}}",
                                3
                            )
                        for i in range(int(cellCount)):
                            self.sensor_registration(
                                frameAddress,
                                f"Cell Resistance #{i+1:02d}",
                                f"cell_resistance_{i+1:02d}",
                                None,
                                "mΩ",
                                None,
                                "state",
                                f"{{{{ value_json.cr{i+1:02d} | float }}}}",
                                3
                            )
                        self.sensor_registration(frameAddress, "Balancing Current", "balancing_current", "current", "A", None, "state", "{{ value_json.bal_current | float }}", 3)
                        self.binary_sensor_registration(frameAddress, "Balancing Enabled", "balancing_enabled", None, None, None, "state", "{{ value_json.bal_enabled }}", 0)
                        self.sensor_registration(frameAddress, "Balancing Mode", "balancing_mode", None, None, None, "state", "{{ value_json.bal_mode }}", None)
                        self.binary_sensor_registration(frameAddress, "Alarm", "alarm", "safety", None, None, "state", "{{ value_json.alarm }}", 0)

                        # diagnostic category
                        self.sensor_registration(frameAddress, "Charge Voltage", "charge_voltage", "voltage", "V", "diagnostic", "settings", "{{ value_json.charge_voltage | float }}", 3)
                        self.sensor_registration(frameAddress, "Float Voltage", "float_voltage", "voltage", "V", "diagnostic", "settings", "{{ value_json.float_voltage | float }}", 3)
                        self.sensor_registration(frameAddress, "Max Charge Current", "max_charge_current", "current", "A", "diagnostic", "settings", "{{ value_json.max_charge_current | float }}", 3)
                        self.sensor_registration(frameAddress, "Max Discharge Current", "max_discharge_current", "current", "A", "diagnostic", "settings", "{{ value_json.max_discharge_current | float }}", 3)
                        self.sensor_registration(frameAddress, "Balance Start Voltage", "balance_start_voltage", "voltage", "V", "diagnostic", "settings", "{{ value_json.balance_start_voltage | float }}", 3)
                        self.sensor_registration(frameAddress, "Balance Trigger Voltage", "balance_trigger_voltage", "voltage", "V", "diagnostic", "settings", "{{ value_json.balance_trigger_voltage | float }}", 5)
                        self.sensor_registration(frameAddress, "Max Balance Current", "max_balance_current", "current", "A", "diagnostic", "settings", "{{ value_json.max_balance_current | float }}", 3)
                        self.sensor_registration(frameAddress, "SOC 100% Voltage", "soc100_voltage", "voltage", "V", "diagnostic", "settings", "{{ value_json.soc100_voltage | float }}", 3)
                        self.sensor_registration(frameAddress, "SOC 0% Voltage", "soc_zero_voltage", "voltage", "V", "diagnostic", "settings", "{{ value_json.soc_zero_voltage | float }}", 3)
                        self.sensor_registration(frameAddress, "Cell UVP", "cell_uvp", "voltage", "V", "diagnostic", "settings", "{{ value_json.cell_uvp | float }}", 3)
                        self.sensor_registration(frameAddress, "Cell OVP", "cell_ovp", "voltage", "V", "diagnostic", "settings", "{{ value_json.cell_ovp | float }}", 3)
                        self.sensor_registration(frameAddress, "Power Off Voltage", "power_off_voltage", "voltage", "V", "diagnostic", "settings", "{{ value_json.power_off_voltage | float }}", 3)
                        self.binary_sensor_registration(frameAddress, "Charge Enabled Switch", "charge_enabled_switch", None, None, "diagnostic", "settings", "{{ value_json.charge_enabled_switch }}")
                        self.binary_sensor_registration(frameAddress, "Discharge Enabled Switch", "discharge_enabled_switch", None, None, "diagnostic", "settings", "{{ value_json.discharge_enabled_switch }}")
                        self.binary_sensor_registration(frameAddress, "Balancer Switch", "balancer_switch", None, None, "diagnostic", "settings", "{{ value_json.balancer_switch }}")
                    else:
                        self.logger.debug(f"{get_timestamp()} Update settings for BMS #{frameAddress}")

                    self.client.publish(
                        f"{self.topic_values}/{frameAddress:02d}/settings",
                        json.dumps({
                            "charge_voltage": truncate(read32(msg.payload, 38) * 0.001, 3),
                            "float_voltage": truncate(read32(msg.payload, 42) * 0.001, 3),
                            "max_charge_current": truncate(read32(msg.payload, 50) * 0.001, 3),
                            "max_discharge_current": truncate(read32(msg.payload, 62) * 0.001, 3),
                            "charge_enabled_switch": "ON" if bool(msg.payload[118]) else "OFF",
                            "discharge_enabled_switch": "ON" if bool(msg.payload[122]) else "OFF",
                            "balance_start_voltage": truncate(read32(msg.payload, 138) * 0.001, 3),
                            "balance_trigger_voltage": truncate(read32(msg.payload, 26) * 0.001, 5),
                            "max_balance_current": truncate(read32(msg.payload, 78) * 0.001, 3),
                            "balancer_switch": "ON" if bool(msg.payload[126]) else "OFF",
                            "soc100_voltage": truncate(read32(msg.payload, 30) * 0.001, 3),
                            "soc_zero_voltage": truncate(read32(msg.payload, 34) * 0.001, 3),
                            "cell_uvp": truncate(read32(msg.payload, 10) * 0.001, 3),
                            "cell_ovp": truncate(read32(msg.payload, 18) * 0.001, 3),
                            "power_off_voltage": truncate(read32(msg.payload, 46) * 0.001, 3)
                        })
                    )

                elif frameType == 0x02 and bms_registered: # decode_jk02_cell_info_
                    self.logger.debug(f"{get_timestamp()} Update Cell Info for BMS #{frameAddress}")
                    cellCount = self.bms_registry[frameAddress]

                    battery_voltage = truncate(read32(msg.payload, 118 + 16*2) * 0.001, 3)
                    battery_current = truncate(read32(msg.payload, 126 + 16*2) * 0.001, 3)
                    balancing_mode = msg.payload[140 + 16*2]
                    alarm1 = msg.payload[134]
                    alarm2 = msg.payload[135]
                    alarm3 = msg.payload[136]

                    state = {
                            "bat_voltage": battery_voltage,
                            "bat_current": battery_current,
                            "bat_power": truncate(battery_current * battery_voltage, 3),
                            "soc": msg.payload[141 + 16*2],
                            "soh": msg.payload[158 + 16*2],
                            "cycles": msg.payload[150 + 16*2],
                            "cap_remaining": truncate(read32(msg.payload, 142 + 16*2) * 0.001, 3),
                            "cap_total": truncate(read32(msg.payload, 146 + 16*2) * 0.001, 3),
                            "temp_mos": truncate(read16(msg.payload, 112 + 16*2) * 0.1, 3),
                            "temp1": truncate(read16(msg.payload, 130 + 16*2) * 0.1, 3),
                            "temp2": truncate(read16(msg.payload, 132 + 16*2) * 0.1, 3),
                            # "temperature_3": truncate(read16(msg.payload, 222 + 16*2) * 0.1, 3), # MOS?
                            "temp3": truncate(read16(msg.payload, 224 + 16*2) * 0.1, 3),
                            "temp4": truncate(read16(msg.payload, 226 + 16*2) * 0.1, 3),
                            "cell_avg_volt": truncate(read16(msg.payload, 58 + 16) * 0.001, 3),
                            "cell_volt_diff": truncate(read16(msg.payload, 60 + 16) * 0.001, 3),
                            "cell_max_index": msg.payload[62 + 16]+1,
                            "cell_min_index": msg.payload[63 + 16]+1,
                            "bal_current": truncate(read16(msg.payload, 138 + 16*2) * 0.001, 3),
                            "bal_enabled": "ON" if bool(msg.payload[140 + 16*2] in [0x01, 0x02]) else "OFF",
                            "bal_mode": "Off" if balancing_mode == 0x00 else ("Charging balancer" if balancing_mode == 0x01 else "Discharging balancer"),
                            "alarm": "ON" if alarm1 != 0 or alarm2 != 0 or alarm3 != 0 else "OFF",
                        }

                    for i in range(int(cellCount)):
                        state[f"cv{i+1:02d}"] = truncate(read16(msg.payload, i*2 + 6) * 0.001, 3)
                        state[f"cr{i+1:02d}"] = truncate(read16(msg.payload, i*2 + 64 + 16) * 0.001, 3)

                    # //  # Bit 0     Wire resistance                              0000 0000 0000 0001         0x0001 
                    # //  # Bit 1     MOS OTP                                      0000 0000 0000 0010         0x0002
                    # //  # Bit 2     Cell quantity                                0000 0000 0000 0100         0x0004
                    # //  # Bit 3     Current sensor error                         0000 0000 0000 1000         0x0008
                    # //  # Bit 4     Cell OVP                                     0000 0000 0001 0000         0x0010
                    # //  # Bit 5     Battery OVP                                  0000 0000 0010 0000         0x0020
                    # //  # Bit 6     Charge OCP                                   0000 0000 0100 0000         0x0040
                    # //  # Bit 7     Charge SCP                                   0000 0000 1000 0000         0x0080
                    # //  # Bit 8     Charge OTP                                   0000 0001 0000 0000         0x0100
                    # //  # Bit 9     Charge UTP                                   0000 0010 0000 0000         0x0200
                    # //  # Bit 10    CPU Aux comm error                           0000 0100 0000 0000         0x0400
                    # //  # Bit 11    Cell UVP                                     0000 1000 0000 0000         0x0800
                    # //  # Bit 12    Batt UVP                                     0001 0000 0000 0000         0x1000
                    # //  # Bit 13    Discharge OCP                                0010 0000 0000 0000         0x2000
                    # //  # Bit 14    Discharge SCP                                0100 0000 0000 0000         0x4000
                    # //  # Bit 15    Charge MOS                                   1000 0000 0000 0000         0x8000
                    # //  # Bit 16    Discharge MOS                           0001 0000 0000 0000 0000        0x10000
                    # //  # Bit 17    GPS Disconneted                         0010 0000 0000 0000 0000        0x20000
                    # //  # Bit 18    Modify PWD. in time                     0100 0000 0000 0000 0000        0x40000
                    # //  # Bit 19    Discharge On Failed                     1000 0000 0000 0000 0000        0x80000
                    # //  # Bit 20    Battery Over Temp Alarm            0001 0000 0000 0000 0000 0000       0x100000
                    # //  # Bit 21    Temperature sensor anomaly         0010 0000 0000 0000 0000 0000       0x200000
                    # //  # Bit 22    PLCModule anomaly                  0100 0000 0000 0000 0000 0000       0x400000
                    # //  # Bit 23    Reserved                           1000 0000 0000 0000 0000 0000       0x800000
                    alarms = []
                    if (check_bit_of_byte(alarm1, 0)):
                        alarms.append("Wire resistance")
                    if (check_bit_of_byte(alarm1, 1)):
                        alarms.append("MOS OTP")
                    if (check_bit_of_byte(alarm1, 2)):
                        alarms.append("Cell quantity")
                    if (check_bit_of_byte(alarm1, 3)):
                        alarms.append("Current sensor error")
                    if (check_bit_of_byte(alarm1, 4)):
                        alarms.append("Cell OVP")
                    if (check_bit_of_byte(alarm1, 5)):
                        alarms.append("Battery OVP")
                    if (check_bit_of_byte(alarm1, 6)):
                        alarms.append("Charge OCP")
                    if (check_bit_of_byte(alarm1, 7)):
                        alarms.append("Charge SCP")
                    if (check_bit_of_byte(alarm2, 0)):
                        alarms.append("Charge OTP")
                    if (check_bit_of_byte(alarm2, 1)):
                        alarms.append("Charge UTP")
                    if (check_bit_of_byte(alarm2, 2)):
                        alarms.append("CPU Aux comm error")
                    if (check_bit_of_byte(alarm2, 3)):
                        alarms.append("Cell UVP")
                    if (check_bit_of_byte(alarm2, 4)):
                        alarms.append("Batt UVP")
                    if (check_bit_of_byte(alarm2, 5)):
                        alarms.append("Discharge OCP")
                    if (check_bit_of_byte(alarm2, 6)):
                        alarms.append("Discharge SCP")
                    if (check_bit_of_byte(alarm2, 7)):
                        alarms.append("Charge MOS")
                    if (check_bit_of_byte(alarm3, 0)):
                        alarms.append("Discharge MOS")
                    if (check_bit_of_byte(alarm3, 1)):
                        alarms.append("GPS Disconnected")
                    if (check_bit_of_byte(alarm3, 2)):
                        alarms.append("Modify PWD in time")
                    if (check_bit_of_byte(alarm3, 3)):
                        alarms.append("Discharge On Failed")
                    if (check_bit_of_byte(alarm3, 4)):
                        alarms.append("Battery Over Temp Alarm")
                    if (check_bit_of_byte(alarm3, 5)):
                        alarms.append("Temperature sensor anomaly")
                    if (check_bit_of_byte(alarm3, 6)):
                        alarms.append("PLC Module anomaly")
                    if (check_bit_of_byte(alarm3, 7)):
                        alarms.append("Reserved")

                    state["alarms"] = alarms

                    self.client.publish(
                        f"{self.topic_values}/{frameAddress:02d}/state",
                        json.dumps(state)
                    )
                else:
                    self.logger.warning(f"{get_timestamp()} Unsupported Frame Type: {frameType} from BMS #{frameAddress}")

            else:
                # self.logger.debug(f"Unknown payload received: '{msg.payload.hex()}' ({len(msg.payload)} bytes)")
                pass
        
        except Exception as e:
            self.logger.error(f"{get_timestamp()} Error processing message: {e}", exc_info=True)
    
    def on_subscribe(self, client, userdata, mid, granted_qos):
        self.logger.info(f"{get_timestamp()} Subscription confirmed with QoS: {granted_qos}")
    
    def print_connection_error(self, rc):
        error_messages = {
            1: "Connection refused - incorrect protocol version",
            2: "Connection refused - invalid client identifier",
            3: "Connection refused - server unavailable",
            4: "Connection refused - bad username or password",
            5: "Connection refused - not authorised"
        }
        if rc in error_messages:
            self.logger.error(f"{get_timestamp()} MQTT Error: {error_messages[rc]}")
        else:
            self.logger.error(f"{get_timestamp()} Unknown MQTT connection error: {rc}")

    def build_sensor_registration(self, address, name, id, device_class, unit_of_measurement, entity_category, value_template = "{{ value }}", precision = 3):
        r = {
                "name": name,
                "unique_id": f"jk_bms_{address:02d}_{id}",
                "state_topic": f"{self.topic_values}/{address:02d}/{id}",
                "value_template": value_template,
                "device_class": device_class,
                "unit_of_measurement": unit_of_measurement,
                "suggested_display_precision": precision,
                "force_update": True,
                "device": {
                    "name": f'JK BMS #{address:02d}',
                    "manufacturer": "JK Battery",
                    "model": "JK Inverter BMS",
                    "identifiers": [
                        f"jk_bms_{address:02d}"
                    ]
                }
            }
        if entity_category is not None:
            r["entity_category"] = entity_category
        return json.dumps(r, indent=4)
    
    def sensor_registration(self, address, name, id, device_class, unit_of_measurement, entity_category, value_topic, value_template = "{{ value }}", precision = 3):
        r = {
                "name": name,
                "unique_id": f"jk_bms_{address:02d}_{id}",
                "state_topic": f"{self.topic_values}/{address:02d}/{value_topic}",
                "value_template": value_template,
                "suggested_display_precision": precision,
                "force_update": True,
                "device": {
                    "name": f'JK BMS #{address:02d}',
                    "manufacturer": "JK Battery",
                    "model": "JK Inverter BMS",
                    "identifiers": [
                        f"jk_bms_{address:02d}"
                    ]
                }
            }
        
        if device_class is not None:
            r["unit_of_measurement"] = unit_of_measurement

        if device_class is not None:
            r["device_class"] = device_class

        if entity_category is not None:
            r["entity_category"] = entity_category

        if precision is None:
            r.pop("suggested_display_precision", None)

        self.client.publish(
            f'{self.topic_registration}/sensor/jk_bms_{address:02d}/{id}/config',
            json.dumps(r, indent=4)
        )

    def binary_sensor_registration(self, address, name, id, device_class, unit_of_measurement, entity_category, value_topic, value_template = "{{ value }}", precision = 3):
        r = {
                "name": name,
                "unique_id": f"jk_bms_{address:02d}_{id}",
                "state_topic": f"{self.topic_values}/{address:02d}/{value_topic}",
                "value_template": value_template,
                "device_class": device_class,
                "unit_of_measurement": unit_of_measurement,
                "suggested_display_precision": precision,
                "force_update": True,
                "device": {
                    "name": f'JK BMS #{address:02d}',
                    "manufacturer": "JK Battery",
                    "model": "JK Inverter BMS",
                    "identifiers": [
                        f"jk_bms_{address:02d}"
                    ]
                }
            }
        if entity_category is not None:
            r["entity_category"] = entity_category

        self.client.publish(
            f'{self.topic_registration}/binary_sensor/jk_bms_{address:02d}/{id}/config',
            json.dumps(r, indent=4)
        )

    def connect_and_listen(self):
        try:
            # Initialize log file
            self.logger.info(f"{get_timestamp()} Logging data to: {os.path.abspath(self.log_file)}")
            
            # Create MQTT client
            self.client = mqtt.Client()
            
            # Set callbacks
            self.client.on_connect = self.on_connect
            self.client.on_message = self.on_message
            self.client.on_disconnect = self.on_disconnect
            self.client.on_subscribe = self.on_subscribe
            
            # Set username and password
            self.client.username_pw_set(self.username, self.password)
            
            self.logger.info(f"{get_timestamp()} Connecting to MQTT broker at {self.broker_host}:{self.broker_port}...")
            
            # Initial connection with retry
            connected = False
            for attempt in range(1, 6):  # Try 5 times
                try:
                    self.logger.info(f"{get_timestamp()} Initial connection attempt {attempt}/5...")
                    self.client.connect(self.broker_host, self.broker_port, 60)
                    connected = True
                    break
                except Exception as e:
                    self.logger.error(f"{get_timestamp()} Initial connection attempt {attempt} failed: {e}")
                    if attempt < 5:
                        time.sleep(5)  # Wait 5 seconds before retry
            
            if not connected:
                self.logger.error(f"{get_timestamp()} Failed to establish initial connection after 5 attempts - exiting")
                sys.exit(1)
            
            # Start the loop
            self.logger.info(f"{get_timestamp()} Starting MQTT client loop...")
            self.logger.info(f"{get_timestamp()} Waiting for RS485 data... (Press Ctrl+C to exit)")
            self.client.loop_forever()
            
        except KeyboardInterrupt:
            self.logger.info(f"{get_timestamp()} Shutting down...")
            if self.client:
                self.client.disconnect()
        except Exception as e:
            self.logger.error(f"{get_timestamp()} Error: {e}", exc_info=True)
            return False
        
        return True


def main():
    """Main function to start the RS485 MQTT client."""
    # MQTT broker configuration from environment variables or defaults
    BROKER_HOST = os.getenv("MQTT_BROKER_HOST", "core-mosquitto")
    BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT", "1883"))
    USERNAME = os.getenv("MQTT_USERNAME", "homeassistant")
    PASSWORD = os.getenv("MQTT_PASSWORD", "")
    TOPIC_TX = os.getenv("TOPIC_TX", "rs485tx/tx")
    TOPIC_VALUES = os.getenv("TOPIC_VALUES", "rs485tx/bms")
    TOPIC_REGISTRATION = os.getenv("TOPIC_REGISTRATION", "homeassistant")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "info")
    
    # Setup logging
    logger = setup_logging(LOG_LEVEL)
    
    logger.info("RS485 MQTT Client for JK-BMS Data")
    logger.info("=" * 40)
    logger.info(f"Broker: {BROKER_HOST}:{BROKER_PORT}")
    logger.info(f"Topic-TX: {TOPIC_TX}")
    logger.info(f"Topic-HA-values: {TOPIC_VALUES}")
    logger.info(f"Topic-HA-registration: {TOPIC_REGISTRATION}")
    logger.info(f"User: {USERNAME}")
    logger.info(f"Log Level: {LOG_LEVEL}")
    logger.info("=" * 40)
    
    # Create and start the client
    client = RS485MQTTClient(BROKER_HOST, BROKER_PORT, USERNAME, PASSWORD, TOPIC_TX, TOPIC_REGISTRATION, TOPIC_VALUES)
    client.connect_and_listen()


if __name__ == "__main__":
    main()
