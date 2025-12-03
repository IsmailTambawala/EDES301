#!/bin/bash
# Simple PocketBeagle startup helper for ACL Rehab Tracker backend.

cd "$(dirname "$0")"

export IMU_THIGH_ADDR="${IMU_THIGH_ADDR:-0x68}"
export IMU_SHIN_ADDR="${IMU_SHIN_ADDR:-0x69}"
export IMU_I2C_BUS="${IMU_I2C_BUS:-2}"

export MYOWARE_ADC_PIN="${MYOWARE_ADC_PIN:-P2_35}"
export MYOWARE_MAX_VOLTAGE="${MYOWARE_MAX_VOLTAGE:-3.3}"
export MYOWARE_ADC_REF_VOLTAGE="${MYOWARE_ADC_REF_VOLTAGE:-3.3}"

sudo config-pin p1_26 i2c
sudo config-pin p1_28 i2c

sudo -E python3 main.py

