from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import os
import time
from sensors.imu import IMUManager
from sensors.myoware import MuscleSensor
from processing import calculate_physics, reset_max_values

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize sensors

def _build_sensor_map():
    def _parse(addr_str: str, fallback: int) -> int:
        if not addr_str:
            return fallback
        addr_str = addr_str.strip().lower()
        return int(addr_str, 16) if addr_str.startswith("0x") else int(addr_str)

    defaults = {"thigh": 0x68, "shin": 0x69}
    sensor_map = {}
    for segment, env_name in (("thigh", "IMU_THIGH_ADDR"), ("shin", "IMU_SHIN_ADDR")):
        sensor_map[segment] = _parse(os.getenv(env_name), defaults[segment])
    return sensor_map


imu_manager = IMUManager(
    bus_id=int(os.getenv("IMU_I2C_BUS", "2")),
    sensor_map=_build_sensor_map(),
)
muscle_sensor = MuscleSensor(
    mock=os.getenv("MUSCLE_MOCK", "false").lower() == "true"
)

pitch_offset_thigh = 0.0
roll_offset_thigh = 0.0
pitch_offset_shin = 0.0
roll_offset_shin = 0.0


def _offsets_for(segment: str):
    if segment == "thigh":
        return pitch_offset_thigh, roll_offset_thigh
    return pitch_offset_shin, roll_offset_shin


def _empty_segment():
    return {
        "pitch": 0.0,
        "roll": 0.0,
        "raw_pitch": 0.0,
        "raw_roll": 0.0,
        "gyro_pitch": 0.0,
        "gyro_roll": 0.0,
        "yaw": 0.0,
        "accel_g": {"x": 0.0, "y": 0.0, "z": 0.0},
        "gyro_dps": {"x": 0.0, "y": 0.0, "z": 0.0},
    }


def _apply_segment_offsets(segment: str, data):
    if not data:
        return _empty_segment()
    pitch_offset, roll_offset = _offsets_for(segment)
    segment_data = {**data}
    segment_data["pitch"] = segment_data.get("pitch", 0.0) - pitch_offset
    segment_data["roll"] = segment_data.get("roll", 0.0) - roll_offset
    return segment_data


def _apply_offsets_all(imu_data):
    if not imu_data:
        return {}
    calibrated = {}
    for segment in imu_data:
        calibrated[segment] = _apply_segment_offsets(segment, imu_data.get(segment))
    return calibrated

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        # Reset max values when new connection starts
        reset_max_values()
        muscle_sensor.clear_reference()
        
        while True:
            # 1. Read Sensor Data
            imu_data = imu_manager.read()
            calibrated_imu = _apply_offsets_all(imu_data)
            muscle_sample = muscle_sensor.read()
            muscle_relative = muscle_sample["relative"]
            muscle_voltage = muscle_sample["voltage"]
            rest_voltage = muscle_sample["rest_voltage"]
            peak_voltage = muscle_sample["peak_voltage"]

            # 2. Process Data
            physics_data = calculate_physics(calibrated_imu, muscle_relative)

            # 3. Send to Client
            payload = {
                "timestamp": time.time(),
                "raw_imu": imu_data,
                "imu": calibrated_imu,
                "muscle_voltage": muscle_voltage,
                "muscle_relative": muscle_relative,
                "muscle_rest_voltage": rest_voltage,
                "muscle_peak_voltage": peak_voltage,
                **physics_data
            }
            await websocket.send_json(payload)
            
            # 30Hz update rate (~33ms per frame)
            await asyncio.sleep(1/30)
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()

@app.post("/reset")
async def reset_session():
    """Reset maximum tracked values"""
    reset_max_values()
    muscle_sensor.clear_reference()
    return {"status": "reset"}


@app.post("/imu/calibrate")
async def calibrate():
    global pitch_offset_thigh, roll_offset_thigh
    global pitch_offset_shin, roll_offset_shin

    readings = imu_manager.read()
    thigh = readings.get("thigh", {})
    shin = readings.get("shin", {})

    pitch_offset_thigh = thigh.get("pitch", 0.0)
    roll_offset_thigh = thigh.get("roll", 0.0)
    pitch_offset_shin = shin.get("pitch", 0.0)
    roll_offset_shin = shin.get("roll", 0.0)
    return {"status": "ok"}


@app.post("/muscle/calibrate")
async def calibrate_muscle(mode: str):
    if mode not in {"rest", "max"}:
        return {"error": "mode must be 'rest' or 'max'"}
    result = muscle_sensor.calibrate_range(mode)
    return result


@app.get("/imu/thigh")
async def get_thigh():
    readings = imu_manager.read()
    return _apply_segment_offsets("thigh", readings.get("thigh"))


@app.get("/imu/shin")
async def get_shin():
    readings = imu_manager.read()
    return _apply_segment_offsets("shin", readings.get("shin"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8010)
