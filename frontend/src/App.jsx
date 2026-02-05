import { useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Shield,
  Upload,
  FileText,
  Activity,
  AlertTriangle,
  Search,
  Zap,
  Lock,
  Server,
  Globe,
  Terminal,
  ChevronRight,
  Sparkles,
  Cpu,
  Network,
  Fingerprint
} from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'

const API_URL = 'http://localhost:5090'

// Animated background particles
const ParticleField = () => {
  const particles = Array.from({ length: 50 }, (_, i) => ({
    id: i,
    x: Math.random() * 100,
    y: Math.random() * 100,
    size: Math.random() * 3 + 1,
    duration: Math.random() * 20 + 10,
    delay: Math.random() * 5
  }))

  return (
    <div className="fixed inset-0 overflow-hidden pointer-events-none">
      {particles.map(p => (
        <motion.div
          key={p.id}
          className="absolute rounded-full bg-primary-500/20"
          style={{
            left: `${p.x}%`,
            top: `${p.y}%`,
            width: p.size,
            height: p.size,
          }}
          animate={{
            y: [0, -100, 0],
            x: [0, Math.random() * 50 - 25, 0],
            opacity: [0, 1, 0],
          }}
          transition={{
            duration: p.duration,
            delay: p.delay,
            repeat: Infinity,
            ease: "linear"
          }}
        />
      ))}
    </div>
  )
}

// Header Component
const Header = () => (
  <motion.header
    initial={{ y: -100 }}
    animate={{ y: 0 }}
    className="fixed top-0 left-0 right-0 z-50 glass-dark"
  >
    <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
      <motion.div
        className="flex items-center gap-3"
        whileHover={{ scale: 1.02 }}
      >
        <div className="relative">
          <Shield className="w-10 h-10 text-primary-400" />
          <motion.div
            className="absolute inset-0 text-primary-400"
            animate={{ opacity: [0.5, 1, 0.5] }}
            transition={{ duration: 2, repeat: Infinity }}
          >
            <Shield className="w-10 h-10" />
          </motion.div>
        </div>
        <div>
          <h1 className="text-2xl font-bold gradient-text">DeepLog</h1>
          <p className="text-xs text-gray-400">Security Analytics Platform</p>
        </div>
      </motion.div>

      <nav className="flex items-center gap-8">
        {[
          { icon: Activity, label: 'Dashboard', href: '#dashboard' },
          { icon: Upload, label: 'Analyze', href: '#analyze' },
          { icon: FileText, label: 'Reports', href: '#reports' },
          { icon: Server, label: 'Live', href: '#live', pulse: true },
        ].map(item => (
          <motion.a
            key={item.label}
            href={item.href}
            className="flex items-center gap-2 text-gray-300 hover:text-white transition-colors"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <item.icon className="w-4 h-4" />
            <span className="text-sm">{item.label}</span>
            {item.pulse && (
              <motion.span
                className="w-2 h-2 bg-green-500 rounded-full"
                animate={{ opacity: [0.5, 1, 0.5] }}
                transition={{ duration: 1.5, repeat: Infinity }}
              />
            )}
          </motion.a>
        ))}
      </nav>

      <motion.div
        className="flex items-center gap-4"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
      >
        <div className="flex items-center gap-2 px-4 py-2 rounded-full glass">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
          <span className="text-xs text-gray-300">System Online</span>
        </div>
      </motion.div>
    </div>
  </motion.header>
)

// Stat Card Component
const StatCard = ({ icon: Icon, label, value, color, delay }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ delay }}
    whileHover={{ y: -5, scale: 1.02 }}
    className="glass rounded-2xl p-6 relative overflow-hidden group"
  >
    <div className={`absolute top-0 right-0 w-32 h-32 rounded-full blur-3xl opacity-20 ${color}`} />
    <div className="relative z-10">
      <motion.div
        className={`w-12 h-12 rounded-xl flex items-center justify-center ${color} bg-opacity-20 mb-4`}
        whileHover={{ rotate: 360 }}
        transition={{ duration: 0.5 }}
      >
        <Icon className="w-6 h-6" />
      </motion.div>
      <motion.div
        className="text-4xl font-bold gradient-text mb-1"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: delay + 0.2 }}
      >
        {value}
      </motion.div>
      <div className="text-sm text-gray-400">{label}</div>
    </div>
  </motion.div>
)

// Threat Level Meter
const ThreatMeter = ({ score }) => {
  const getColor = (s) => {
    if (s >= 8) return 'from-red-500 to-red-600'
    if (s >= 5) return 'from-yellow-500 to-orange-500'
    return 'from-green-500 to-emerald-500'
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      className="glass rounded-2xl p-8"
    >
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-yellow-500" />
          Threat Level
        </h3>
        <motion.span
          className={`text-4xl font-bold gradient-text`}
          key={score}
          initial={{ scale: 1.2 }}
          animate={{ scale: 1 }}
        >
          {score}/10
        </motion.span>
      </div>
      <div className="h-4 bg-gray-800 rounded-full overflow-hidden">
        <motion.div
          className={`h-full bg-gradient-to-r ${getColor(score)}`}
          initial={{ width: 0 }}
          animate={{ width: `${score * 10}%` }}
          transition={{ duration: 1, ease: "easeOut" }}
        />
      </div>
      <div className="flex justify-between mt-2 text-xs text-gray-500">
        <span>Low</span>
        <span>Medium</span>
        <span>High</span>
        <span>Critical</span>
      </div>
    </motion.div>
  )
}

// Attack Type Chart
const AttackChart = ({ data }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    className="glass rounded-2xl p-6"
  >
    <h3 className="text-lg font-semibold mb-6 flex items-center gap-2">
      <Network className="w-5 h-5 text-primary-400" />
      Attack Distribution
    </h3>
    <ResponsiveContainer width="100%" height={250}>
      <BarChart data={data}>
        <XAxis dataKey="name" stroke="#64748b" fontSize={12} />
        <YAxis stroke="#64748b" fontSize={12} />
        <Tooltip
          contentStyle={{
            background: 'rgba(15, 23, 42, 0.9)',
            border: '1px solid rgba(102, 126, 234, 0.3)',
            borderRadius: '8px',
          }}
        />
        <Bar dataKey="value" radius={[4, 4, 0, 0]}>
          {data.map((_, index) => (
            <Cell key={`cell-${index}`} fill={`hsl(${240 + index * 40}, 70%, 60%)`} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  </motion.div>
)

// File Upload Zone
const UploadZone = ({ onAnalyze, loading }) => {
  const [dragActive, setDragActive] = useState(false)
  const [file, setFile] = useState(null)
  const [logs, setLogs] = useState('')
  const [mode, setMode] = useState('upload') // 'upload' or 'paste'

  const handleDrag = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }, [])

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    if (e.dataTransfer.files?.[0]) {
      setFile(e.dataTransfer.files[0])
    }
  }, [])

  const handleFileChange = (e) => {
    if (e.target.files?.[0]) {
      setFile(e.target.files[0])
    }
  }

  const handleAnalyze = async () => {
    if (mode === 'upload' && file) {
      const formData = new FormData()
      formData.append('file', file)
      await onAnalyze(formData)
    } else if (mode === 'paste' && logs.trim()) {
      await onAnalyze({ logs })
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass rounded-2xl p-8"
    >
      <div className="flex gap-4 mb-6">
        {['upload', 'paste'].map(m => (
          <motion.button
            key={m}
            onClick={() => setMode(m)}
            className={`flex items-center gap-2 px-6 py-3 rounded-xl transition-all ${
              mode === m
                ? 'bg-primary-600 text-white'
                : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
            }`}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            {m === 'upload' ? <Upload className="w-4 h-4" /> : <Terminal className="w-4 h-4" />}
            {m === 'upload' ? 'Upload File' : 'Paste Logs'}
          </motion.button>
        ))}
      </div>

      <AnimatePresence mode="wait">
        {mode === 'upload' ? (
          <motion.div
            key="upload"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <div
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              className={`relative border-2 border-dashed rounded-2xl p-12 text-center transition-all ${
                dragActive
                  ? 'border-primary-500 bg-primary-500/10'
                  : 'border-gray-600 hover:border-primary-400'
              }`}
            >
              <input
                type="file"
                onChange={handleFileChange}
                accept=".log,.txt,.json"
                className="absolute inset-0 opacity-0 cursor-pointer"
              />
              {file ? (
                <motion.div
                  initial={{ scale: 0.8 }}
                  animate={{ scale: 1 }}
                  className="flex flex-col items-center"
                >
                  <FileText className="w-16 h-16 text-primary-400 mb-4" />
                  <p className="text-lg font-medium">{file.name}</p>
                  <p className="text-sm text-gray-400">
                    {(file.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </motion.div>
              ) : (
                <motion.div
                  initial={{ scale: 0.9 }}
                  animate={{ scale: 1 }}
                  className="flex flex-col items-center"
                >
                  <motion.div
                    animate={{ y: [0, -10, 0] }}
                    transition={{ duration: 2, repeat: Infinity }}
                  >
                    <Upload className="w-16 h-16 text-gray-500 mb-4" />
                  </motion.div>
                  <p className="text-lg font-medium mb-2">
                    Drag & drop your log file
                  </p>
                  <p className="text-sm text-gray-400">
                    or click to browse (.log, .txt, .json)
                  </p>
                </motion.div>
              )}
            </div>
          </motion.div>
        ) : (
          <motion.div
            key="paste"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <textarea
              value={logs}
              onChange={(e) => setLogs(e.target.value)}
              placeholder="Paste your log content here..."
              className="w-full h-48 bg-gray-900/50 border border-gray-700 rounded-xl p-4 text-sm font-mono text-gray-300 resize-none focus:outline-none focus:border-primary-500"
            />
          </motion.div>
        )}
      </AnimatePresence>

      <motion.button
        onClick={handleAnalyze}
        disabled={loading || (!file && !logs.trim())}
        className="w-full mt-6 py-4 bg-gradient-to-r from-primary-600 to-purple-600 rounded-xl font-semibold text-white flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
      >
        {loading ? (
          <>
            <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            Analyzing...
          </>
        ) : (
          <>
            <Sparkles className="w-5 h-5" />
            Start Analysis
            <ChevronRight className="w-5 h-5" />
          </>
        )}
      </motion.button>
    </motion.div>
  )
}

// Event List
const EventList = ({ events }) => {
  // Safety check for events
  if (!events || events.length === 0) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass rounded-2xl p-6"
      >
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Fingerprint className="w-5 h-5 text-primary-400" />
          Detected Threats
        </h3>
        <p className="text-gray-400 text-center py-8">No threats detected</p>
      </motion.div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass rounded-2xl p-6"
    >
      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
        <Fingerprint className="w-5 h-5 text-primary-400" />
        Detected Threats
      </h3>
      <div className="space-y-3 max-h-96 overflow-y-auto">
        {events.map((event, i) => {
          const severity = (event.threat_level || event.severity || 'medium').toLowerCase()
          return (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.05 }}
              className={`p-4 rounded-xl border-l-4 ${
                severity === 'critical'
                  ? 'border-red-500 bg-red-500/10'
                  : severity === 'high'
                  ? 'border-orange-500 bg-orange-500/10'
                  : 'border-yellow-500 bg-yellow-500/10'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium">{event.attack_type || 'Unknown'}</span>
                <span className={`px-2 py-1 rounded-full text-xs font-bold ${
                  severity === 'critical'
                    ? 'bg-red-500/20 text-red-400'
                    : severity === 'high'
                    ? 'bg-orange-500/20 text-orange-400'
                    : 'bg-yellow-500/20 text-yellow-400'
                }`}>
                  {severity.toUpperCase()}
                </span>
              </div>
              <p className="text-sm text-gray-400 mb-2">{event.description || ''}</p>
              <code className="text-xs bg-gray-900/50 px-2 py-1 rounded block truncate">
                {event.raw_log || ''}
              </code>
            </motion.div>
          )
        })}
      </div>
    </motion.div>
  )
}

// Dashboard Grid
const DashboardGrid = ({ results }) => (
  <motion.div
    initial={{ opacity: 0 }}
    animate={{ opacity: 1 }}
    transition={{ delay: 0.3 }}
    className="grid grid-cols-1 lg:grid-cols-4 gap-6 mb-6"
  >
    <StatCard
      icon={AlertTriangle}
      label="Critical"
      value={results.critical}
      color="bg-red-500"
      delay={0.4}
    />
    <StatCard
      icon={AlertTriangle}
      label="High Risk"
      value={results.high}
      color="bg-orange-500"
      delay={0.5}
    />
    <StatCard
      icon={Search}
      label="Medium"
      value={results.medium}
      color="bg-yellow-500"
      delay={0.6}
    />
    <StatCard
      icon={Activity}
      label="Total Events"
      value={results.total}
      color="bg-primary-500"
      delay={0.7}
    />
  </motion.div>
)

// Feature Cards
const Features = () => (
  <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mt-12">
    {[
      { icon: Cpu, title: 'Deep Learning', desc: 'LSTM-based anomaly detection', color: 'from-blue-500 to-cyan-500' },
      { icon: Lock, title: 'MITRE ATT&CK', desc: 'Enterprise security framework', color: 'from-purple-500 to-pink-500' },
      { icon: Globe, title: 'Multi-Format', desc: 'Support 10+ log formats', color: 'from-orange-500 to-red-500' },
      { icon: Zap, title: 'Real-time', desc: 'Live stream analysis', color: 'from-green-500 to-emerald-500' },
    ].map((feature, i) => (
      <motion.div
        key={i}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.8 + i * 0.1 }}
        whileHover={{ y: -5 }}
        className="glass rounded-2xl p-6 cursor-pointer group"
      >
        <motion.div
          className={`w-12 h-12 rounded-xl bg-gradient-to-br ${feature.color} flex items-center justify-center mb-4`}
          whileHover={{ rotate: 360 }}
          transition={{ duration: 0.5 }}
        >
          <feature.icon className="w-6 h-6 text-white" />
        </motion.div>
        <h3 className="font-semibold mb-1">{feature.title}</h3>
        <p className="text-sm text-gray-400">{feature.desc}</p>
      </motion.div>
    ))}
  </div>
)

// Main App
function App() {
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState(null)

  const handleAnalyze = async (data) => {
    setLoading(true)
    try {
      const endpoint = data instanceof FormData ? '/api/analyze' : '/api/quick-analyze'
      const response = await fetch(`${API_URL}${endpoint}`, {
        method: 'POST',
        body: data instanceof FormData ? data : JSON.stringify(data),
        headers: data instanceof FormData ? {} : { 'Content-Type': 'application/json' },
      })
      const result = await response.json()
      if (result.success) {
        setResults({
          critical: result.summary.critical,
          high: result.summary.high,
          medium: result.summary.medium,
          total: result.summary.total_events,
          threatScore: result.summary.threat_score,
          attackTypes: Object.entries(result.summary.attack_types).map(([name, value]) => ({ name, value })),
          events: result.detected_events || [],
        })
      }
    } catch (error) {
      console.error('Analysis failed:', error)
      alert('Failed to connect to backend. Make sure Flask server is running on port 5000.')
    }
    setLoading(false)
  }

  return (
    <div className="min-h-screen grid-bg">
      <ParticleField />
      <Header />

      <main className="pt-32 pb-20 px-6">
        <div className="max-w-7xl mx-auto">
          {/* Hero Section */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center mb-12"
          >
            <motion.div
              className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass mb-6"
              animate={{ opacity: [0.7, 1, 0.7] }}
              transition={{ duration: 3, repeat: Infinity }}
            >
              <Shield className="w-4 h-4 text-primary-400" />
              <span className="text-sm text-gray-300">Next-Gen Security Analytics</span>
            </motion.div>
            <h1 className="text-5xl md:text-7xl font-bold mb-4">
              <span className="gradient-text">DeepLog</span>
              <span className="text-white"> Security</span>
            </h1>
            <p className="text-xl text-gray-400 max-w-2xl mx-auto">
              Advanced threat detection powered by DeepLog LSTM neural networks
            </p>
          </motion.div>

          {/* Analysis Section */}
          <section id="analyze" className="mb-12">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="max-w-3xl mx-auto"
            >
              <UploadZone onAnalyze={handleAnalyze} loading={loading} />
            </motion.div>
          </section>

          {/* Results Section */}
          {results && (
            <motion.section
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="mb-12"
            >
              <DashboardGrid results={results} />
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <ThreatMeter score={results.threatScore} />
                <AttackChart data={results.attackTypes} />
              </div>
              <EventList events={results.events} />
            </motion.section>
          )}

          <Features />
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-800 py-8">
        <div className="max-w-7xl mx-auto px-6 text-center text-gray-500 text-sm">
          <p>DeepLog Security Analyzer | Based on DeepLog (CCS'17) & MITRE ATT&CK</p>
        </div>
      </footer>
    </div>
  )
}

export default App
