# ACL Rehab Tracker

This guide walks a new operator through setting up and running the ACL Rehab Tracker system: a PocketBeagle-based backend that streams IMU + MyoWare data, and a React frontend that visualizes live knee movement and muscle activation. For a complete guide on the hardware for this project refer to the hackster page.

---

## 1. System at a Glance

| Component | Hardware | Software | Purpose |
| --- | --- | --- | --- |
| Backend | PocketBeagle + 2× MPU6050 IMUs + MyoWare sensor | Python / FastAPI (`backend/`) | Reads sensors and streams data over WebSockets on port `8010`. |
| Frontend | Your laptop/desktop | Node.js / React (`frontend/`) | Connects to the PocketBeagle backend at `http://192.168.7.2:8010` and renders the UI. |

**Important:** Only copy the `backend/` folder to the PocketBeagle. Only copy the `frontend/` folder to your laptop. You do not need the entire repository in both places.

---

## 2. Prepare the PocketBeagle (Backend)

### 2.1. Clone the repository on the PocketBeagle

1. SSH into the PocketBeagle (`ssh debian@192.168.7.2`).
2. Clone this repository:
   ```bash
   git clone ...
   ```
3. Keep only the backend on the device:
   ```bash
   cd ACL-Rehab-Tracker-Codebase
   rm -rf frontend
   ```
4. (Optional) Move the backend folder somewhere convenient:
   ```bash
   mv backend ~/acl-tracker-backend
   cd ~/acl-tracker-backend
   ```

### 2.2. Install Python dependencies

The backend requires Python 3 and the packages listed in `requirements.txt`. Install them once:

```bash
sudo python3 -m pip install -r requirements.txt
```

(If you prefer a virtual environment, activate it before running the command.)

### 2.3. Configure and test the startup script

The `backend/start_beagle.sh` script exports sensor settings, configures the ADC pin, and launches `main.py` with `sudo`. Make it executable:

```bash
chmod +x start_beagle.sh
```

Run it manually to confirm everything works:

```bash
./start_beagle.sh
```

You should see log lines from Uvicorn indicating the backend is running on `0.0.0.0:8010`. Stop it with `Ctrl+C` when you’re done testing.

#### Environment variables used by the script

You can override these before running `start_beagle.sh` if your hardware differs:

| Variable | Default | Description |
| --- | --- | --- |
| `IMU_THIGH_ADDR` | `0x68` | I²C address of the thigh IMU. |
| `IMU_SHIN_ADDR` | `0x69` | I²C address of the shin IMU. |
| `IMU_I2C_BUS` | `2` | PocketBeagle I²C bus wired to the sensors. |
| `MYOWARE_ADC_PIN` | `P2_35` | Analog pin (3.3 V capable) for the MyoWare output. |
| `MYOWARE_MAX_VOLTAGE` | `3.3` | Maximum expected sensor voltage on that pin. |
| `MYOWARE_ADC_REF_VOLTAGE` | `3.3` | ADC reference voltage. |

### 2.4. Launch on boot (recommended)

After you’ve tested `start_beagle.sh`, add it to the `root` crontab so it runs on every boot.

```bash
sudo crontab -e
```

Add the following line (adjust the path if your backend lives elsewhere):

```
@reboot sleep 60 && bash /home/debian/acl-tracker-backend/backend/start_beagle.sh >> /home/debian/acl-tracker-backend/backend/cron.log 2>&1
```

Notes:

- `sleep 60` gives the PocketBeagle a minute to finish booting before sensors are initialized.
- All stdout/stderr is appended to `cron.log`. Check this file if you suspect the backend failed to start.

---

## 3. Prepare Your Laptop (Frontend)

### 3.1. Copy frontend files

Clone the repository on your laptop/desktop and keep only the frontend:

```bash
git clone https://github.com/<your-org>/ACL-Rehab-Tracker-Codebase.git
cd ACL-Rehab-Tracker-Codebase
rm -rf backend
cd frontend
```

### 3.2. Install Node.js dependencies

Inside the `frontend/` directory:

```bash
npm install
```

### 3.3. Run the development server

```bash
npm run dev
```

Vite prints the local URL (default `http://localhost:5173`). Leave this terminal running while you use the app.

### 3.4. Confirm the laptop can reach the PocketBeagle

- Ensure the USB networking interface is up (your laptop should get an address like `192.168.7.x`).
- You should be able to reach `http://192.168.7.2:8010` from the laptop. If not, check cabling and PocketBeagle power.

---

## 4. Running a Training Session

1. **Start the backend**
   - If you set up the service, just power the PocketBeagle and wait ~10 seconds.
   - Otherwise, SSH in and run `./start_beagle.sh`.

2. **Start the frontend**
   - On your laptop: `npm run dev`.
   - Open `http://localhost:5173` in a Chromium-based browser for best results.

3. **Guided calibration**
   - Click **Initialize Sensors**.
   - Step 1: Keep the athlete’s leg straight and muscles relaxed; click “Capture Resting Baseline.” This captures the MyoWare resting voltage and zeros the IMUs.
   - Step 2: Have the athlete squeeze as hard as possible; click “Capture Max Squeeze.” This stores the 100 % reference for the relative muscle bar.
   - The button now reads **Recalibrate** in case you need to repeat the procedure.

4. **Monitor metrics**
   - Relative muscle activation bar shows the current effort as a percentage between the calibrated rest and max voltages.
   - Knee animation and flexion/extension cards update in real time from the IMUs.
   - Charts display historical traces for angles, torque, and muscle activation.

5. **Resetting**
   - Press **Reset Session** at the top to clear history and max values (it does not rerun calibration).

---

## 5. Troubleshooting Checklist

| Issue | Checks |
| --- | --- |
| **Frontend shows “Disconnected”** | Confirm the backend is running (`systemctl status acl-tracker.service` or console logs), and that the laptop can reach `192.168.7.2`. |
| **No sensor movement** | Run `i2cdetect -r 2` on the PocketBeagle to ensure both IMUs respond (`0x68` and `0x69`). Check wiring/order of sensors. |
| **Muscle bar stuck** | Make sure `config-pin P2_35 ain` succeeds. Verify the sensor output stays within 0–3.3 V. Re-run the calibration flow and hold the contraction until the capture completes. |
| **Permission errors when starting backend** | Ensure `start_beagle.sh` has execute permission and is run with `sudo` (the script already uses `sudo -E python3 main.py`). |
| **Frontend cannot connect but backend is running** | Check that the laptop firewall allows outgoing connections to `192.168.7.2:8010`. |

---

## 6. File Reference

- `backend/start_beagle.sh`: Boot helper used by the systemd service or manual starts.
- `backend/main.py`: FastAPI/WebSocket server.
- `backend/sensors/imu.py`: PocketBeagle IMU manager for dual MPU6050s.
- `backend/sensors/myoware.py`: MyoWare ADC reader with rest/max calibration.
- `frontend/src/App.jsx`: Main React application with calibration flow and UI components.
- `frontend/src/config.js`: API base URL (defaults to `http://192.168.7.2:8010`; update if your PocketBeagle uses a different IP).



