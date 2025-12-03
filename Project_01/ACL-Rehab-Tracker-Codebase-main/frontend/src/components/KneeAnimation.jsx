function KneeAnimation({ flexionAngle, extensionAngle, maxFlexion, maxExtension }) {
  // Normalize angles for visualization
  // Flexion: 0-180 degrees (0 = straight, 180 = fully bent)
  // We'll visualize as a knee joint bending
  
  // Convert flexion angle to SVG rotation (0° = straight leg, 90° = 90° bend)
  // For visualization, we'll show the shin rotating relative to thigh
  const shinRotation = flexionAngle // Direct mapping
  
  // Calculate positions for visualization
  const thighLength = 120
  const shinLength = 100
  
  // Thigh is mostly vertical with slight angle
  const thighAngle = 10 // Slight forward lean
  
  // Shin rotates relative to thigh
  const shinAngle = thighAngle + shinRotation
  
  // Calculate endpoint positions - knee joint is the connection point
  const kneeX = 200
  const kneeY = 150
  
  // Thigh starts from hip and ends at knee joint
  const thighStartX = kneeX - thighLength * Math.sin(Math.PI * thighAngle / 180)
  const thighStartY = kneeY - thighLength * Math.cos(Math.PI * thighAngle / 180)
  // Thigh ends exactly at knee joint
  const thighEndX = kneeX
  const thighEndY = kneeY
  
  // Shin starts exactly at knee joint and extends downward
  const shinEndX = kneeX + shinLength * Math.sin(Math.PI * shinAngle / 180)
  const shinEndY = kneeY + shinLength * Math.cos(Math.PI * shinAngle / 180)
  
  // Max angle visualization
  const maxShinAngle = thighAngle + maxFlexion
  const maxShinEndX = kneeX + shinLength * Math.sin(Math.PI * maxShinAngle / 180)
  const maxShinEndY = kneeY + shinLength * Math.cos(Math.PI * maxShinAngle / 180)

  return (
    <div className="w-full">
      <svg viewBox="0 0 400 300" className="w-full h-auto">
        {/* Background circle for joint */}
        <circle cx={kneeX} cy={kneeY} r="8" fill="#4B5563" />
        
        {/* Max flexion indicator (dashed line) */}
        <line
          x1={kneeX}
          y1={kneeY}
          x2={maxShinEndX}
          y2={maxShinEndY}
          stroke="#9333EA"
          strokeWidth="2"
          strokeDasharray="5,5"
          opacity="0.5"
        />
        
        {/* Thigh (upper leg) - connects from hip to knee */}
        <line
          x1={thighStartX}
          y1={thighStartY}
          x2={thighEndX}
          y2={thighEndY}
          stroke="#3B82F6"
          strokeWidth="14"
          strokeLinecap="round"
        />
        
        {/* Shin (lower leg) - connects from knee to ankle */}
        <line
          x1={kneeX}
          y1={kneeY}
          x2={shinEndX}
          y2={shinEndY}
          stroke="#10B981"
          strokeWidth="14"
          strokeLinecap="round"
        />
        
        {/* Knee joint circle - overlays the connection point */}
        <circle cx={kneeX} cy={kneeY} r="12" fill="#6366F1" stroke="#fff" strokeWidth="3" />
        
        {/* Angle arc indicator */}
        <path
          d={`M ${kneeX + 30 * Math.sin(Math.PI * thighAngle / 180)} ${kneeY - 30 * Math.cos(Math.PI * thighAngle / 180)} 
              A 30 30 0 ${shinRotation > 90 ? 1 : 0} 1 ${kneeX + 30 * Math.sin(Math.PI * shinAngle / 180)} ${kneeY + 30 * Math.cos(Math.PI * shinAngle / 180)}`}
          fill="none"
          stroke="#F59E0B"
          strokeWidth="2"
          opacity="0.7"
        />
        
        {/* Angle text */}
        <text
          x={kneeX + 40}
          y={kneeY + 20}
          fill="#F59E0B"
          fontSize="14"
          fontWeight="bold"
        >
          {flexionAngle.toFixed(0)}°
        </text>
        
        {/* Labels */}
        <text x={thighStartX - 20} y={thighStartY} fill="#3B82F6" fontSize="12" fontWeight="bold">
          Thigh
        </text>
        <text x={shinEndX + 10} y={shinEndY} fill="#10B981" fontSize="12" fontWeight="bold">
          Shin
        </text>
      </svg>
      
      {/* Range indicators */}
      <div className="mt-4 grid grid-cols-2 gap-4">
        <div className="bg-blue-50 p-3 rounded-lg">
          <div className="text-xs text-gray-600 mb-1">Flexion Range</div>
          <div className="text-lg font-bold text-blue-600">
            0° → {maxFlexion.toFixed(1)}°
          </div>
        </div>
        <div className="bg-green-50 p-3 rounded-lg">
          <div className="text-xs text-gray-600 mb-1">Extension Range</div>
          <div className="text-lg font-bold text-green-600">
            180° → {maxExtension.toFixed(1)}°
          </div>
        </div>
      </div>
    </div>
  )
}

export default KneeAnimation

