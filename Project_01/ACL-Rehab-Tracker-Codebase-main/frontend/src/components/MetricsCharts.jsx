import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ComposedChart, Bar } from 'recharts'

function MetricsCharts({ history }) {
  // Prepare data for charts
  const chartData = history.map((item, index) => ({
    time: index,
    timestamp: new Date(item.timestamp * 1000).toLocaleTimeString(),
    muscleRelative: item.muscle_relative || 0,
    flexion: item.flexion_angle || 0,
    extension: item.extension_angle || 180,
    torque: item.torque || 0,
  }))

  // If no data, show empty state
  if (chartData.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        <p>No data yet. Start moving to see metrics!</p>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Flexion/Extension Chart */}
      <div>
        <h3 className="text-lg font-semibold mb-4 text-gray-700">Knee Flexion & Extension Angles</h3>
        <ResponsiveContainer width="100%" height={250}>
          <ComposedChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis 
              dataKey="time" 
              label={{ value: 'Time (samples)', position: 'insideBottom', offset: -5 }}
              stroke="#6b7280"
            />
            <YAxis 
              label={{ value: 'Angle (degrees)', angle: -90, position: 'insideLeft' }}
              domain={[0, 180]}
              stroke="#6b7280"
            />
            <Tooltip 
              contentStyle={{ backgroundColor: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px' }}
              labelFormatter={(value) => `Sample ${value}`}
            />
            <Legend />
            <Line 
              type="monotone" 
              dataKey="flexion" 
              stroke="#3b82f6" 
              strokeWidth={2}
              dot={false}
              name="Flexion (degrees)"
            />
            <Line 
              type="monotone" 
              dataKey="extension" 
              stroke="#10b981" 
              strokeWidth={2}
              dot={false}
              name="Extension (degrees)"
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Torque Chart */}
      <div>
      {/* Muscle Activation Chart */}
      <div>
        <h3 className="text-lg font-semibold mb-4 text-gray-700">Muscle Activation</h3>
        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis 
              dataKey="time" 
              label={{ value: 'Time (samples)', position: 'insideBottom', offset: -5 }}
              stroke="#6b7280"
            />
            <YAxis 
              label={{ value: 'Activation (%)', angle: -90, position: 'insideLeft' }}
              domain={[0, 100]}
              stroke="#6b7280"
            />
            <Tooltip 
              contentStyle={{ backgroundColor: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px' }}
              labelFormatter={(value) => `Sample ${value}`}
            />
            <Legend />
            <Line 
              type="monotone" 
              dataKey="muscleRelative" 
              stroke="#a855f7" 
              strokeDasharray="5 5"
              strokeWidth={2}
              dot={false}
              name="Relative (%)"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
        <h3 className="text-lg font-semibold mb-4 text-gray-700">Torque Over Time</h3>
        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis 
              dataKey="time" 
              label={{ value: 'Time (samples)', position: 'insideBottom', offset: -5 }}
              stroke="#6b7280"
            />
            <YAxis 
              label={{ value: 'Torque (N⋅m)', angle: -90, position: 'insideLeft' }}
              stroke="#6b7280"
            />
            <Tooltip 
              contentStyle={{ backgroundColor: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px' }}
              labelFormatter={(value) => `Sample ${value}`}
            />
            <Legend />
            <Line 
              type="monotone" 
              dataKey="torque" 
              stroke="#8b5cf6" 
              strokeWidth={2}
              dot={false}
              name="Torque (N⋅m)"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Combined Overview Chart */}
      <div>
        <h3 className="text-lg font-semibold mb-4 text-gray-700">All Metrics Overview</h3>
        <ResponsiveContainer width="100%" height={300}>
          <ComposedChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis 
              dataKey="time" 
              label={{ value: 'Time (samples)', position: 'insideBottom', offset: -5 }}
              stroke="#6b7280"
            />
            <YAxis 
              yAxisId="left"
              label={{ value: 'Angle / Activation', angle: -90, position: 'insideLeft' }}
              stroke="#6b7280"
            />
            <YAxis 
              yAxisId="right" 
              orientation="right"
              label={{ value: 'Torque (N⋅m)', angle: 90, position: 'insideRight' }}
              stroke="#6b7280"
            />
            <Tooltip 
              contentStyle={{ backgroundColor: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px' }}
              labelFormatter={(value) => `Sample ${value}`}
            />
            <Legend />
            <Line 
              yAxisId="left"
              type="monotone" 
              dataKey="flexion" 
              stroke="#3b82f6" 
              strokeWidth={2}
              dot={false}
              name="Flexion (degrees)"
            />
            <Line 
              yAxisId="left"
              type="monotone" 
              dataKey="extension" 
              stroke="#10b981" 
              strokeWidth={2}
              dot={false}
              name="Extension (degrees)"
            />
            <Line 
              yAxisId="left"
              type="monotone" 
              dataKey="muscleRelative" 
              stroke="#a855f7" 
              strokeWidth={2}
              dot={false}
              name="Muscle Relative (%)"
            />
            <Line 
              yAxisId="right"
              type="monotone" 
              dataKey="torque" 
              stroke="#8b5cf6" 
              strokeWidth={2}
              dot={false}
              name="Torque (N⋅m)"
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

export default MetricsCharts

