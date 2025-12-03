import { useEffect, useState } from 'react'

function MuscleActivationBar({ value, difficulty, threshold = 100, label, showThreshold = true, showStatus = true }) {
  const [displayValue, setDisplayValue] = useState(0)
  const [isActive, setIsActive] = useState(false)

  useEffect(() => {
    // Smooth animation for bar value
    const timer = setTimeout(() => {
      setDisplayValue(value)
      // Bar is "active" if value exceeds threshold for current difficulty
      setIsActive(value >= threshold)
    }, 50)
    return () => clearTimeout(timer)
  }, [value, threshold])

  // Calculate bar height (0-100%)
  const barHeight = Math.min(100, Math.max(0, displayValue))
  
  // Color based on whether threshold is met
  const barColor = isActive 
    ? 'bg-green-500' 
    : displayValue >= threshold * 0.7 
      ? 'bg-yellow-500' 
      : 'bg-red-500'

  return (
    <div className="w-full">
      {label && <p className="text-sm font-semibold text-gray-600 mb-2">{label}</p>}
      {/* Bar Container */}
      <div className="relative bg-gray-200 rounded-lg h-64 overflow-hidden shadow-inner">
        {/* Threshold Line */}
        {showThreshold && (
          <div
            className="absolute left-0 right-0 border-t-2 border-dashed border-purple-600 z-10"
            style={{ bottom: `${threshold}%` }}
          >
            {showThreshold && (
              <div className="absolute right-2 -top-3 bg-purple-600 text-white text-xs px-2 py-1 rounded">
                Level {difficulty} Threshold ({threshold}%)
              </div>
            )}
          </div>
        )}

        {/* Animated Bar */}
        <div
          className={`absolute bottom-0 left-0 right-0 ${barColor} transition-all duration-300 ease-out rounded-lg`}
          style={{ height: `${barHeight}%` }}
        >
          {/* Shimmer effect when active */}
          {isActive && showThreshold && (
            <div className="absolute inset-0 bg-gradient-to-t from-transparent via-white to-transparent opacity-30 animate-pulse"></div>
          )}
        </div>

        {/* Value Display */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className={`text-6xl font-bold ${showThreshold ? (isActive ? 'text-green-700' : 'text-gray-600') : 'text-gray-800'} transition-colors`}>
            {displayValue.toFixed(0)}%
          </div>
        </div>
      </div>

      {/* Status Indicator */}
      {showStatus && (
        <div className="mt-4 flex items-center justify-center gap-2">
          <div className={`w-4 h-4 rounded-full ${isActive ? 'bg-green-500 animate-pulse' : 'bg-gray-400'}`}></div>
          <span className={`font-semibold ${isActive ? 'text-green-600' : 'text-gray-600'}`}>
            {isActive ? 'Threshold Met!' : `Need ${threshold}% to activate`}
          </span>
        </div>
      )}
    </div>
  )
}

export default MuscleActivationBar

