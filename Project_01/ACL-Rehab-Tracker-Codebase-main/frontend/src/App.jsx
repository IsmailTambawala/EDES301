import { useState, useEffect, useRef, useMemo } from 'react'
import MuscleActivationBar from './components/MuscleActivationBar'
import KneeAnimation from './components/KneeAnimation'
import MetricsCharts from './components/MetricsCharts'
import { Activity, Zap, RotateCcw } from 'lucide-react'
import { API_BASE_URL } from './config'

const backendBase = API_BASE_URL.replace(/\/$/, '')
const websocketBase = backendBase.replace(/^http/i, 'ws')

function App() {
  const createNeutralImu = () => ({
    thigh: { pitch: 0, roll: 0 },
    shin: { pitch: 0, roll: 0 }
  })

  const [data, setData] = useState(null)
  const [isConnected, setIsConnected] = useState(false)
  const [difficulty, setDifficulty] = useState(1) // 1-5 difficulty levels
  const [history, setHistory] = useState([])
  const [smoothImu, setSmoothImu] = useState(() => createNeutralImu())
  const [isCalibrating, setIsCalibrating] = useState(false)
  const [toastMessage, setToastMessage] = useState(null)
  const [muscleRange, setMuscleRange] = useState({ rest: null, peak: null })
  const [calibrationStep, setCalibrationStep] = useState("ready") // ready -> rest -> peak -> done
  const [modalState, setModalState] = useState({ type: null, open: false })
  const wsRef = useRef(null)
  const toastTimeoutRef = useRef(null)
  const maxHistoryLength = 100 // Keep last 100 data points for charts
  const smoothingAlpha = 0.8

  useEffect(() => {
    connectWebSocket()
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
      if (toastTimeoutRef.current) {
        clearTimeout(toastTimeoutRef.current)
      }
    }
  }, [])

  const connectWebSocket = () => {
    const ws = new WebSocket(`${websocketBase}/ws`)
    wsRef.current = ws

    ws.onopen = () => {
      console.log('Connected to WebSocket')
      setIsConnected(true)
    }

    ws.onmessage = (event) => {
      const newData = JSON.parse(event.data)
      setData(newData)
      if (Object.prototype.hasOwnProperty.call(newData, 'muscle_rest_voltage')) {
        setMuscleRange({
          rest: newData.muscle_rest_voltage ?? null,
          peak: newData.muscle_peak_voltage ?? null,
        })
      }
      const imuPayload = newData?.imu || newData?.raw_imu || {}
      setSmoothImu((prev) => {
        const previous = prev || createNeutralImu()
        const segments = ['thigh', 'shin']
        const updated = {}
        segments.forEach((segment) => {
          const prevSegment = previous[segment] || { pitch: 0, roll: 0 }
          const incoming = imuPayload?.[segment]
          if (!incoming) {
            updated[segment] = prevSegment
            return
          }
          const newPitch = incoming.pitch ?? prevSegment.pitch
          const newRoll = incoming.roll ?? prevSegment.roll
          updated[segment] = {
            pitch: smoothingAlpha * prevSegment.pitch + (1 - smoothingAlpha) * newPitch,
            roll: smoothingAlpha * prevSegment.roll + (1 - smoothingAlpha) * newRoll
          }
        })
        return updated
      })
      
      // Add to history for charts
      setHistory(prev => {
        const updated = [...prev, newData]
        return updated.slice(-maxHistoryLength)
      })
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      setIsConnected(false)
    }

    ws.onclose = () => {
      console.log('WebSocket disconnected')
      setIsConnected(false)
      // Attempt to reconnect after 3 seconds
      setTimeout(connectWebSocket, 3000)
    }
  }

  const resetSession = async () => {
    try {
      await fetch(`${backendBase}/reset`, { method: 'POST' })
      setHistory([])
      setMuscleRange({ rest: null, peak: null })
      setCalibrationStep("ready")
    } catch (error) {
      console.error('Failed to reset session:', error)
    }
  }

  const calibrateImu = async () => {
    await fetch(`${backendBase}/imu/calibrate`, { method: 'POST' })
    setSmoothImu(createNeutralImu())
  }

  const calibrateMuscleStep = async (mode) => {
    const response = await fetch(`${backendBase}/muscle/calibrate?mode=${mode}`, { method: 'POST' })
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }
    const result = await response.json()
    setMuscleRange({
      rest: result.rest_voltage ?? muscleRange.rest,
      peak: result.peak_voltage ?? muscleRange.peak,
    })
  }

  const openModal = (type) => {
    setModalState({ type, open: true })
  }

  const closeModal = () => {
    setModalState({ type: null, open: false })
  }

  const handleModalConfirm = async () => {
    try {
      setIsCalibrating(true)
      if (calibrationStep === "rest") {
        await calibrateMuscleStep("rest")
        await calibrateImu()
        setCalibrationStep("peak")
      } else if (calibrationStep === "peak") {
        await calibrateMuscleStep("max")
        if (toastTimeoutRef.current) {
          clearTimeout(toastTimeoutRef.current)
        }
        setToastMessage('Calibration complete. Relative meter now spans your relaxed → max contraction.')
        toastTimeoutRef.current = setTimeout(() => setToastMessage(null), 3000)
        setCalibrationStep("done")
        closeModal()
      }
    } catch (error) {
      console.error('Calibration failed:', error)
    } finally {
      setIsCalibrating(false)
    }
  }

  const difficultyLevels = [
    { level: 1, name: 'Very Easy', threshold: 20 },
    { level: 2, name: 'Easy', threshold: 35 },
    { level: 3, name: 'Medium', threshold: 50 },
    { level: 4, name: 'Hard', threshold: 65 },
    { level: 5, name: 'Very Hard', threshold: 80 }
  ]

  const relativePeak = useMemo(() => {
    if (!history.length) return 0
    return Math.max(...history.map((entry) => entry.muscle_relative ?? 0))
  }, [history])

  const currentRelative = data?.muscle_relative ?? 0
  const muscleVoltage = data?.muscle_voltage ?? 0

  const modalCopy = {
    unified: {
      title: 'Initialize Sensors',
      description:
        calibrationStep === "rest"
          ? 'Relax completely with the sensor in place; we will capture the resting baseline.'
          : 'Squeeze as hard as possible while keeping your leg straight; we will capture the max effort.',
      checklist:
        calibrationStep === "rest"
          ? [
              'Sit upright, leg straight, muscles relaxed.',
              'Ensure electrodes have solid contact.',
              'Press confirm while staying relaxed.',
            ]
          : [
              'Keep the same setup.',
              'Flex the target muscle as hard as possible.',
              'Press confirm while still squeezing.',
            ],
      confirmLabel:
        calibrationStep === "rest"
          ? 'Capture Resting Baseline'
          : 'Capture Max Squeeze',
      confirmDisabled: isCalibrating,
    },
  }

  const openUnifiedModal = () => {
    setModalState({ type: 'unified', open: true })
    setCalibrationStep("rest")
  }

  return (
    <div className="min-h-screen p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-800 mb-2">
                ACL Rehab Tracker
              </h1>
              <div className="flex items-center gap-2">
                <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
                <span className="text-sm text-gray-600">
                  {isConnected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
            </div>
            <button
              onClick={resetSession}
              className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
            >
              <RotateCcw size={20} />
              Reset Session
            </button>
          </div>
        </div>

        {/* Calibration + Status */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <h2 className="text-xl font-semibold text-gray-800">Initialization</h2>
              <p className="text-sm text-gray-600">
                Calibrate IMUs and muscle sensor in one guided flow.
              </p>
            </div>
            <button
              onClick={openUnifiedModal}
              className={`px-4 py-2 rounded-lg text-white flex items-center justify-center ${
                calibrationStep === 'done' ? 'bg-green-600 hover:bg-green-700' : 'bg-indigo-500 hover:bg-indigo-600'
              } transition-colors`}
            >
              {calibrationStep === 'done' ? 'Recalibrate' : 'Initialize Sensors'}
            </button>
          </div>
          {toastMessage && (
            <div className="mt-4 text-sm text-green-700 bg-green-50 border border-green-200 rounded-lg px-4 py-2">
              {toastMessage}
            </div>
          )}
          <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
            {['thigh', 'shin'].map((segment) => (
              <div key={segment} className="border rounded-lg p-4 bg-gray-50">
                <div className="text-xs font-semibold uppercase text-gray-500 tracking-wide">
                  {segment === 'thigh' ? 'Thigh IMU' : 'Shin IMU'}
                </div>
                <div className="mt-2 text-gray-700">
                  Pitch:{' '}
                  <span className="font-semibold">
                    {(smoothImu?.[segment]?.pitch ?? 0).toFixed(1)}°
                  </span>
                </div>
                <div className="text-gray-700">
                  Roll:{' '}
                  <span className="font-semibold">
                    {(smoothImu?.[segment]?.roll ?? 0).toFixed(1)}°
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Difficulty Selector */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4 text-gray-800">Difficulty Level</h2>
          <div className="flex gap-2">
            {difficultyLevels.map((level) => (
              <button
                key={level.level}
                onClick={() => setDifficulty(level.level)}
                className={`flex-1 px-4 py-3 rounded-lg font-medium transition-all ${
                  difficulty === level.level
                    ? 'bg-purple-600 text-white shadow-lg scale-105'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                <div className="font-bold">{level.level}</div>
                <div className="text-xs">{level.name}</div>
                <div className="text-xs opacity-75">Threshold: {level.threshold}%</div>
              </button>
            ))}
          </div>
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* Muscle Activation Section */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="flex items-center gap-2 mb-4">
              <Zap className="text-yellow-500" size={24} />
              <div>
                <h2 className="text-xl font-semibold text-gray-800">Muscle Activation</h2>
                <p className="text-sm text-gray-500">Relative effort vs. resting baseline</p>
              </div>
            </div>
            <MuscleActivationBar
              label="Relative Activation"
              value={currentRelative}
              difficulty={difficulty}
              threshold={difficultyLevels[difficulty - 1].threshold}
              showThreshold={true}
              showStatus={true}
            />
            <div className="mt-3 text-sm text-gray-600">
              Relative peak: {relativePeak.toFixed(1)}%
            </div>
            <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-gray-600">
              <div className="p-3 bg-gray-50 rounded-lg">
                <div className="text-xs uppercase font-semibold text-gray-500">Instant Voltage</div>
                <div className="text-lg font-bold text-gray-800">{muscleVoltage.toFixed(3)} V</div>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg">
                <div className="text-xs uppercase font-semibold text-gray-500">Calibration Range</div>
                <div className="text-lg font-bold text-gray-800">
                  {muscleRange.rest && muscleRange.peak
                    ? `${muscleRange.rest.toFixed(3)} V → ${muscleRange.peak.toFixed(3)} V`
                    : 'Calibrate to set ranges'}
                </div>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="flex items-center gap-2 mb-4">
              <Activity className="text-blue-500" size={24} />
              <h2 className="text-xl font-semibold text-gray-800">Knee Movement</h2>
            </div>
            <KneeAnimation
              flexionAngle={data?.flexion_angle || 0}
              extensionAngle={data?.extension_angle || 180}
              maxFlexion={data?.max_flexion || 0}
              maxExtension={data?.max_extension || 180}
            />
            <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
              <div>
                <div className="text-gray-600">Current Flexion</div>
                <div className="text-2xl font-bold text-blue-600">
                  {data?.flexion_angle?.toFixed(1) || 0}°
                </div>
              </div>
              <div>
                <div className="text-gray-600">Max Flexion</div>
                <div className="text-2xl font-bold text-purple-600">
                  {data?.max_flexion?.toFixed(1) || 0}°
                </div>
              </div>
              <div>
                <div className="text-gray-600">Current Extension</div>
                <div className="text-2xl font-bold text-green-600">
                  {data?.extension_angle?.toFixed(1) || 180}°
                </div>
              </div>
              <div>
                <div className="text-gray-600">Max Extension</div>
                <div className="text-2xl font-bold text-orange-600">
                  {data?.max_extension?.toFixed(1) || 180}°
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Torque Display */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4 text-gray-800">Torque</h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-gray-600 mb-2">Current Torque</div>
              <div className="text-4xl font-bold text-indigo-600">
                {data?.torque?.toFixed(2) || 0} N⋅m
              </div>
            </div>
            <div>
              <div className="text-gray-600 mb-2">Max Torque</div>
              <div className="text-4xl font-bold text-red-600">
                {data?.max_torque?.toFixed(2) || 0} N⋅m
              </div>
            </div>
          </div>
        </div>

        {/* Charts */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-xl font-semibold mb-4 text-gray-800">Metrics Over Time</h2>
          <MetricsCharts history={history} />
        </div>
      </div>

      {modalState.open && modalCopy[modalState.type] && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
          <div className="bg-white rounded-2xl shadow-2xl max-w-lg w-full p-6">
            <h3 className="text-2xl font-bold text-gray-800 mb-2">{modalCopy[modalState.type].title}</h3>
            <p className="text-gray-600 mb-4">{modalCopy[modalState.type].description}</p>
            <ul className="list-disc pl-5 space-y-2 text-gray-700 mb-6">
              {modalCopy[modalState.type].checklist.map((item, idx) => (
                <li key={idx}>{item}</li>
              ))}
            </ul>
            <div className="flex gap-3">
              <button
                onClick={handleModalConfirm}
                disabled={modalCopy[modalState.type].confirmDisabled}
                className={`flex-1 py-3 rounded-lg font-semibold text-white ${
                  modalCopy[modalState.type].confirmDisabled
                    ? 'bg-gray-400 cursor-not-allowed'
                    : 'bg-indigo-600 hover:bg-indigo-700'
                } transition-colors`}
              >
                {modalCopy[modalState.type].confirmLabel}
              </button>
              <button
                onClick={closeModal}
                className="flex-1 py-3 rounded-lg font-semibold text-gray-700 border border-gray-300 hover:bg-gray-100 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default App

