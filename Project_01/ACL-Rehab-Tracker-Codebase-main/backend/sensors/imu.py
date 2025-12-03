import logging
import math
import time
from contextlib import suppress
from typing import Any, Dict, Optional

try:  # pragma: no cover - hardware specific optional dependency
    import board  # type: ignore
except ImportError:
    board = None  # type: ignore

try:  # pragma: no cover - hardware specific optional dependency
    import busio  # type: ignore
except ImportError:
    busio = None  # type: ignore

try:  # pragma: no cover - hardware specific optional dependency
    import adafruit_mpu6050  # type: ignore
except ImportError:
    adafruit_mpu6050 = None  # type: ignore

try:
    from smbus2 import SMBus  # type: ignore
except ImportError:  # pragma: no cover - handled dynamically
    SMBus = None  # type: ignore


class IMUManager:
    """
    Minimal MPU6050 interface for the PocketBeagle I2C pins (P1_26 SDA / P1_28 SCL).

    The manager can service one or more sensors. Provide a `sensor_map` that maps
    human-readable names (e.g. "shin") to their 7-bit I2C address. When only a
    single sensor is connected (common when prototyping), downstream consumers
    will still receive both `thigh` and `shin` keys—the missing one is populated
    with the available reading so that processors written for dual sensors do not
    crash.
    """

    REG_PWR_MGMT_1 = 0x6B
    REG_SMPLRT_DIV = 0x19
    REG_CONFIG = 0x1A
    REG_GYRO_CONFIG = 0x1B
    REG_ACCEL_CONFIG = 0x1C
    REG_ACCEL_XOUT_H = 0x3B
    REG_GYRO_XOUT_H = 0x43

    ACCEL_SCALE = {2: 16384.0, 4: 8192.0, 8: 4096.0, 16: 2048.0}
    GYRO_SCALE = {250: 131.0, 500: 65.5, 1000: 32.8, 2000: 16.4}
    STANDARD_GRAVITY = 9.80665  # m/s^2
    RAD_TO_DEG = 180.0 / math.pi

    def __init__(
        self,
        bus_id: int = 2,
        sensor_map: Optional[Dict[str, int]] = None,
        accel_range_g: int = 2,
        gyro_range_dps: int = 250,
        dlpf_cfg: int = 3,
    ):
        self.logger = logging.getLogger(__name__)
        self.bus_id = bus_id
        self.sensor_map = sensor_map or {"thigh": 0x68, "shin": 0x69}
        self.accel_range_g = accel_range_g
        self.gyro_range_dps = gyro_range_dps
        self.dlpf_cfg = dlpf_cfg

        self._accel_scale = self.ACCEL_SCALE.get(accel_range_g, 16384.0)
        self._gyro_scale = self.GYRO_SCALE.get(gyro_range_dps, 131.0)
        self.alpha = 0.85
        self.complementary_gain = 0.98
        self.last_time: Optional[float] = None
        self.pitch_f = {name: 0.0 for name in self.sensor_map}
        self.roll_f = {name: 0.0 for name in self.sensor_map}
        self._sensor_state = {
            name: self._default_state() for name in self.sensor_map
        }
        self._bus: Optional[SMBus] = None  # type: ignore[assignment]
        self._i2c: Optional[Any] = None
        self._adafruit_sensors: Dict[str, Any] = {}
        self._backend: Optional[str] = None
        self.start_time = time.time()

        self._setup_hardware()

    def _setup_hardware(self) -> None:
        if self._init_adafruit_driver():
            self._backend = "adafruit"
            return

        if self._init_smbus_driver():
            self._backend = "smbus"
            return

        raise RuntimeError(
            "Unable to initialize any IMU backend. Verify wiring, I2C bus, and drivers."
        )

    def _init_adafruit_driver(self) -> bool:
        if board is None or busio is None or adafruit_mpu6050 is None:
            return False

        try:
            self._i2c = busio.I2C(board.SCL, board.SDA)  # type: ignore[attr-defined]
            self._adafruit_sensors = {}
            for label, addr in self.sensor_map.items():
                self._adafruit_sensors[label] = adafruit_mpu6050.MPU6050(  # type: ignore[attr-defined]
                    self._i2c, address=addr
                )
            self.logger.info("Initialized IMU via adafruit_mpu6050 driver")
            return True
        except Exception as exc:  # pragma: no cover - hardware specific
            self.logger.warning("Unable to init adafruit_mpu6050: %s", exc)
            self._adafruit_sensors = {}
            if self._i2c and hasattr(self._i2c, "deinit"):
                with suppress(Exception):
                    self._i2c.deinit()
            self._i2c = None
            return False

    def _init_smbus_driver(self) -> bool:
        if SMBus is None:
            self.logger.warning("smbus2 not available on this platform")
            return False

        try:
            self._bus = SMBus(self.bus_id)
            self._configure_sensors()
            return True
        except Exception as exc:  # pragma: no cover - hardware specific
            self.logger.warning("Unable to open I2C bus %s: %s", self.bus_id, exc)
            if self._bus:
                with suppress(Exception):
                    self._bus.close()
            self._bus = None
            return False

    def _configure_sensors(self) -> None:
        assert self._bus is not None  # for type-checkers
        for label, addr in self.sensor_map.items():
            try:
                # Wake sensor
                self._bus.write_byte_data(addr, self.REG_PWR_MGMT_1, 0x00)
                # Sample rate ~1 kHz / (1 + divider)
                self._bus.write_byte_data(addr, self.REG_SMPLRT_DIV, 0x07)
                # Digital low-pass filter setting
                self._bus.write_byte_data(addr, self.REG_CONFIG, self.dlpf_cfg & 0x07)
                # Gyro full-scale config
                gyro_cfg = (self._range_to_bits(self.gyro_range_dps) << 3) & 0x18
                self._bus.write_byte_data(addr, self.REG_GYRO_CONFIG, gyro_cfg)
                # Accelerometer full-scale config
                accel_cfg = (self._range_to_bits(self.accel_range_g) << 3) & 0x18
                self._bus.write_byte_data(addr, self.REG_ACCEL_CONFIG, accel_cfg)
                time.sleep(0.01)
            except Exception as exc:  # pragma: no cover - hardware specific
                self.logger.error(
                    "Failed to configure sensor '%s' at 0x%02X: %s", label, addr, exc
                )
                raise

    @staticmethod
    def _range_to_bits(value: int) -> int:
        lookup = {2: 0, 4: 1, 8: 2, 16: 3, 250: 0, 500: 1, 1000: 2, 2000: 3}
        return lookup.get(value, 0)

    def _default_state(self) -> Dict[str, Any]:
        return {
            "yaw": 0.0,
            "last_ts": None,
            "comp_pitch": 0.0,
            "comp_roll": 0.0,
            "pitch_f": 0.0,
            "roll_f": 0.0,
            "filter_initialized": False,
        }

    def _state_for(self, label: str) -> Dict[str, Any]:
        if label not in self._sensor_state:
            self._sensor_state[label] = self._default_state()
            self.pitch_f[label] = 0.0
            self.roll_f[label] = 0.0
        return self._sensor_state[label]

    def read(self):
        if self._backend == "smbus" and self._bus is None:  # pragma: no cover
            raise RuntimeError("I2C bus is not initialized")
        if self._backend == "adafruit" and not self._adafruit_sensors:
            raise RuntimeError("AdaFruit IMU sensors are not initialized")

        now = time.monotonic()
        frame_dt = 0.0 if self.last_time is None else max(0.0, now - self.last_time)
        self.last_time = now

        readings = {}
        for label, addr in self.sensor_map.items():
            try:
                readings[label] = self._read_sensor(label, addr, frame_dt)
            except Exception as exc:
                self.logger.error(
                    "IMU read failed for sensor '%s' (0x%02X): %s", label, addr, exc
                )
                readings[label] = self._empty_orientation(label, error=str(exc))

        return readings

    def _read_sensor(self, label: str, addr: int, frame_dt: float):
        if self._backend == "adafruit":
            return self._read_sensor_adafruit(label, frame_dt)
        return self._read_sensor_smbus(label, addr, frame_dt)

    def _read_sensor_adafruit(self, label: str, frame_dt: float):
        sensor = self._adafruit_sensors.get(label)
        if sensor is None:
            raise RuntimeError(f"No adafruit_mpu6050 instance for sensor '{label}'")

        ax_mps2, ay_mps2, az_mps2 = sensor.acceleration
        gx_rads, gy_rads, gz_rads = sensor.gyro

        ax = (ax_mps2 or 0.0) / self.STANDARD_GRAVITY
        ay = (ay_mps2 or 0.0) / self.STANDARD_GRAVITY
        az = (az_mps2 or 0.0) / self.STANDARD_GRAVITY

        gx = (gx_rads or 0.0) * self.RAD_TO_DEG
        gy = (gy_rads or 0.0) * self.RAD_TO_DEG
        gz = (gz_rads or 0.0) * self.RAD_TO_DEG

        accel_roll = math.degrees(math.atan2(ay, az))
        accel_pitch = math.degrees(math.atan2(-ax, math.sqrt(ay * ay + az * az)))

        yaw = self._integrate_yaw(label, gz)
        filtered = self._apply_filters(
            label,
            accel_pitch=accel_pitch,
            accel_roll=accel_roll,
            gyro_pitch=gy,
            gyro_roll=gx,
            dt=frame_dt,
        )

        return {
            "pitch": float(filtered["pitch"]),
            "roll": float(filtered["roll"]),
            "raw_pitch": float(filtered["raw_pitch"]),
            "raw_roll": float(filtered["raw_roll"]),
            "gyro_pitch": float(filtered["gyro_pitch"]),
            "gyro_roll": float(filtered["gyro_roll"]),
            "yaw": float(yaw),
            "accel_g": {"x": ax, "y": ay, "z": az},
            "gyro_dps": {"x": gx, "y": gy, "z": gz},
        }

    def _read_sensor_smbus(self, label: str, addr: int, frame_dt: float):
        assert self._bus is not None
        ax = self._read_word_2c(addr, self.REG_ACCEL_XOUT_H) / self._accel_scale
        ay = self._read_word_2c(addr, self.REG_ACCEL_XOUT_H + 2) / self._accel_scale
        az = self._read_word_2c(addr, self.REG_ACCEL_XOUT_H + 4) / self._accel_scale

        gx = self._read_word_2c(addr, self.REG_GYRO_XOUT_H) / self._gyro_scale
        gy = self._read_word_2c(addr, self.REG_GYRO_XOUT_H + 2) / self._gyro_scale
        gz = self._read_word_2c(addr, self.REG_GYRO_XOUT_H + 4) / self._gyro_scale

        # Pitch / roll from accelerometer tilt (simple complementary approach).
        accel_roll = math.degrees(math.atan2(ay, az))
        accel_pitch = math.degrees(math.atan2(-ax, math.sqrt(ay * ay + az * az)))

        yaw = self._integrate_yaw(label, gz)
        filtered = self._apply_filters(
            label,
            accel_pitch=accel_pitch,
            accel_roll=accel_roll,
            gyro_pitch=gy,
            gyro_roll=gx,
            dt=frame_dt,
        )

        return {
            "pitch": float(filtered["pitch"]),
            "roll": float(filtered["roll"]),
            "raw_pitch": float(filtered["raw_pitch"]),
            "raw_roll": float(filtered["raw_roll"]),
            "gyro_pitch": float(filtered["gyro_pitch"]),
            "gyro_roll": float(filtered["gyro_roll"]),
            "yaw": float(yaw),
            "accel_g": {"x": ax, "y": ay, "z": az},
            "gyro_dps": {"x": gx, "y": gy, "z": gz},
        }

    def _apply_filters(
        self,
        label: str,
        accel_pitch: float,
        accel_roll: float,
        gyro_pitch: float,
        gyro_roll: float,
        dt: float,
    ):
        state = self._state_for(label)
        if not state["filter_initialized"]:
            state["comp_pitch"] = accel_pitch
            state["comp_roll"] = accel_roll
            state["pitch_f"] = accel_pitch
            state["roll_f"] = accel_roll
            state["filter_initialized"] = True
        comp_pitch = state["comp_pitch"]
        comp_roll = state["comp_roll"]
        if dt > 0.0:
            comp_pitch = (
                self.complementary_gain * (comp_pitch + gyro_pitch * dt)
                + (1 - self.complementary_gain) * accel_pitch
            )
            comp_roll = (
                self.complementary_gain * (comp_roll + gyro_roll * dt)
                + (1 - self.complementary_gain) * accel_roll
            )
        else:
            comp_pitch = accel_pitch
            comp_roll = accel_roll

        prev_pitch_f = state["pitch_f"]
        prev_roll_f = state["roll_f"]
        pitch_filtered = self.alpha * prev_pitch_f + (1 - self.alpha) * comp_pitch
        roll_filtered = self.alpha * prev_roll_f + (1 - self.alpha) * comp_roll

        state["comp_pitch"] = comp_pitch
        state["comp_roll"] = comp_roll
        state["pitch_f"] = pitch_filtered
        state["roll_f"] = roll_filtered
        self.pitch_f[label] = pitch_filtered
        self.roll_f[label] = roll_filtered

        return {
            "pitch": pitch_filtered,
            "roll": roll_filtered,
            "raw_pitch": accel_pitch,
            "raw_roll": accel_roll,
            "gyro_pitch": gyro_pitch,
            "gyro_roll": gyro_roll,
        }

    def _empty_orientation(self, label: str, error: Optional[str] = None):
        state = self._state_for(label)
        payload = {
            "pitch": 0.0,
            "roll": 0.0,
            "yaw": float(state.get("yaw", 0.0)),
            "raw_pitch": 0.0,
            "raw_roll": 0.0,
            "gyro_pitch": 0.0,
            "gyro_roll": 0.0,
            "accel_g": {"x": 0.0, "y": 0.0, "z": 0.0},
            "gyro_dps": {"x": 0.0, "y": 0.0, "z": 0.0},
        }
        if error:
            payload["error"] = error
        return payload

    def _integrate_yaw(self, label: str, gz_dps: float) -> float:
        state = self._state_for(label)
        now = time.monotonic()
        last_ts = state["last_ts"]
        state["last_ts"] = now
        if last_ts is None:
            return state["yaw"]

        dt = now - last_ts
        state["yaw"] += gz_dps * dt
        if state["yaw"] > 180:
            state["yaw"] -= 360
        elif state["yaw"] < -180:
            state["yaw"] += 360
        return state["yaw"]

    def _read_word_2c(self, addr: int, register: int) -> int:
        assert self._bus is not None
        high = self._bus.read_byte_data(addr, register)
        low = self._bus.read_byte_data(addr, register + 1)
        value = (high << 8) + low
        if value >= 0x8000:
            return -((65535 - value) + 1)
        return value

    def __del__(self):  # pragma: no cover - cleanup helper
        if self._bus:
            with suppress(Exception):
                self._bus.close()
        if self._i2c and hasattr(self._i2c, "deinit"):
            with suppress(Exception):
                self._i2c.deinit()
