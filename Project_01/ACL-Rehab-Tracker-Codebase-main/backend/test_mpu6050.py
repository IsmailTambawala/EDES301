import argparse
import json
import time

from sensors.imu import IMUManager


def _parse_sensor_map(values):
    if not values:
        return {"thigh": 0x68, "shin": 0x69}

    sensor_map = {}
    for value in values:
        if "=" not in value:
            raise ValueError(f"Invalid sensor mapping '{value}', use label=0x68 format")
        label, addr = value.split("=", 1)
        label = label.strip().lower()
        addr = addr.strip().lower()
        sensor_map[label] = int(addr, 16) if addr.startswith("0x") else int(addr)
    return sensor_map


def main():
    parser = argparse.ArgumentParser(
        description="Quick sanity-check reader for an MPU6050 connected to the PocketBeagle."
    )
    parser.add_argument(
        "--bus",
        type=int,
        default=2,
        help="I2C bus number (PocketBeagle I2C-2 is exposed on P1_26 / P1_28, defaults to 2).",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=0.5,
        help="Seconds between reads (default: 0.5s).",
    )
    parser.add_argument(
        "--sensor",
        action="append",
        default=[],
        help="Sensor mapping in the form label=0x68. Repeat per sensor. Defaults to shin=0x68.",
    )

    args = parser.parse_args()
    sensor_map = _parse_sensor_map(args.sensor)

    try:
        imu = IMUManager(bus_id=args.bus, sensor_map=sensor_map)
    except RuntimeError as exc:
        parser.error(str(exc))

    print("Press Ctrl+C to stop...\n")
    try:
        while True:
            data = imu.read()
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] {json.dumps(data, indent=2)}")
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nStopping IMU test.")


if __name__ == "__main__":
    main()

