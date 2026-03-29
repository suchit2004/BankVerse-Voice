import { useState, useRef, useEffect } from 'react'

function App() {
  const [isRecording, setIsRecording] = useState(false)
  const [messages, setMessages] = useState([])
  const [guidancePrompt, setGuidancePrompt] = useState('Waiting for conversation to begin...')
  const [summary, setSummary] = useState(null)
  const [isDarkMode, setIsDarkMode] = useState(true)
  const ws = useRef(null)
  const mediaRecorderRef = useRef(null)

  useEffect(() => {
    // Connect to Backend WebSocket
    ws.current = new WebSocket('ws://localhost:8000/ws/audio')
    
    ws.current.onopen = () => console.log('WebSocket Connected')
    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === "summary") {
        setSummary(data.content)
      } else {
        setMessages(prev => [...prev, data])
        if (data.prompt) setGuidancePrompt(data.prompt)
        
        if (data.audio_base64) {
          const snd = new Audio("data:audio/mp3;base64," + data.audio_base64);
          snd.play().catch(e => console.error("Audio playback failed:", e));
        } else if (data.regional_response) {
          const synth = window.speechSynthesis;
          synth.cancel(); // Cancel any ongoing speech
          const utterance = new SpeechSynthesisUtterance(data.regional_response);
          utterance.lang = "mr-IN"; // Use Marathi voice if available
          utterance.rate = 1.0;
          synth.speak(utterance);
        }
      }
    }
    
    return () => {
      if (ws.current) ws.current.close()
    }
  }, [])

  const toggleRecording = async () => {
    if (isRecording) {
      if (mediaRecorderRef.current) {
        mediaRecorderRef.current.stop()
        mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop())
      }
      setIsRecording(false)
    } else {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
        mediaRecorderRef.current = new MediaRecorder(stream)
        
        const audioChunks = []
        mediaRecorderRef.current.ondataavailable = (event) => {
          if (event.data.size > 0) {
            audioChunks.push(event.data)
          }
        }

        mediaRecorderRef.current.onstop = () => {
          const audioBlob = new Blob(audioChunks, { type: 'audio/webm' })
          if (ws.current && ws.current.readyState === WebSocket.OPEN) {
             ws.current.send(audioBlob)
          }
        }

        mediaRecorderRef.current.start()
        setIsRecording(true)
      } catch (err) {
        console.error("Error accessing microphone", err)
        alert("Microphone access is required.")
      }
    }
  }

  return (
    <div className={`relative min-h-screen font-sans transition-colors duration-300 overflow-x-hidden ${isDarkMode ? 'bg-slate-950 text-slate-300 selection:bg-pink-500/30' : 'bg-slate-50 text-slate-700 selection:bg-pink-500/20'}`}>
      
      {/* Subtle Mesh Background using Pink, Blue, Green */}
      <div className={`absolute inset-0 z-0 pointer-events-none transition-opacity duration-700 ${isDarkMode ? 'opacity-[0.15]' : 'opacity-30'}`}>
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-pink-400 blur-[100px]"></div>
        <div className="absolute top-[20%] right-[-5%] w-[30%] h-[30%] rounded-full bg-blue-400 blur-[100px]"></div>
        <div className="absolute bottom-[-10%] left-[20%] w-[40%] h-[40%] rounded-full bg-emerald-400 blur-[120px]"></div>
      </div>

      <main className="relative z-10 max-w-7xl mx-auto p-6 md:p-8 min-h-screen flex flex-col pb-12">
        {/* Header */}
        <header className={`flex justify-between items-center mb-8 pb-5 border-b transition-colors duration-300 ${isDarkMode ? 'border-slate-800/60' : 'border-slate-200/60'}`}>
          <div>
            <h1 className={`text-2xl font-semibold tracking-tight ${isDarkMode ? 'text-slate-100' : 'text-slate-900'}`}>
              BankVerse <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-pink-400 to-emerald-400">Voice</span>
            </h1>
            <p className={`text-sm mt-1 ${isDarkMode ? 'text-slate-500' : 'text-slate-500'}`}>Frontline Staff Assistant</p>
          </div>
          <div className="flex items-center gap-4">
            <button 
              onClick={() => setIsDarkMode(!isDarkMode)}
              className={`p-2 rounded-full transition-colors duration-300 backdrop-blur-md ${isDarkMode ? 'bg-slate-800/80 hover:bg-slate-700 text-slate-300' : 'bg-white/80 hover:bg-white text-slate-600 border border-slate-200/80 shadow-sm'}`}
              title="Toggle Theme"
            >
              {isDarkMode ? (
                // Sun Icon
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
              ) : (
                // Moon Icon
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                </svg>
              )}
            </button>
            <div className={`flex items-center gap-3 px-4 py-2 rounded-full border transition-colors duration-300 backdrop-blur-md ${isDarkMode ? 'bg-slate-900/40 border-slate-800/60' : 'bg-white/60 border-slate-200/60 shadow-sm'}`}>
              <span className="relative flex h-2 w-2">
                {isRecording && <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75"></span>}
                <span className={`relative inline-flex rounded-full h-2 w-2 ${isRecording ? 'bg-rose-500' : 'bg-emerald-500'}`}></span>
              </span>
              <span className={`text-sm font-medium ${isDarkMode ? 'text-slate-300' : 'text-slate-700'}`}>{isRecording ? "Listening" : "System Active"}</span>
            </div>
          </div>
        </header>

        {/* Dashboard Content */}
        <div className="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Main Transcription Area */}
          <div className="lg:col-span-2 flex flex-col space-y-6">
            <div className={`flex-1 min-h-[400px] overflow-y-auto pr-2 space-y-4 scrollbar-thin ${isDarkMode ? 'scrollbar-thumb-slate-800/80' : 'scrollbar-thumb-slate-300/80'}`}>
              {messages.length === 0 ? (
                <div className={`flex flex-col items-center justify-center h-full ${isDarkMode ? 'text-slate-600' : 'text-slate-400'}`}>
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-10 w-10 mb-3 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                  </svg>
                  <p className="text-sm font-medium">No active conversation</p>
                </div>
              ) : (
                messages.map((msg, idx) => (
                  <div key={idx} className={`border rounded-xl p-5 backdrop-blur-sm transition-colors duration-200 ${isDarkMode ? 'bg-slate-900/40 border-slate-800/60 hover:bg-slate-900/60' : 'bg-white/70 border-white/40 hover:bg-white/90 shadow-sm'}`}>
                    <div className="flex items-start justify-between mb-3">
                      <span className={`text-[11px] font-medium uppercase tracking-wider px-2 py-1 rounded ${isDarkMode ? 'text-blue-400 bg-blue-500/10' : 'text-blue-700 bg-blue-100'}`}>
                        {msg.speaker}
                      </span>
                    </div>
                    <div className="space-y-3">
                      <div>
                        <p className={`text-[11px] mb-1 uppercase tracking-wide ${isDarkMode ? 'text-slate-500' : 'text-slate-400'}`}>Transcript</p>
                        <p className={`text-base ${isDarkMode ? 'text-slate-300' : 'text-slate-700'}`}>{msg.transcript}</p>
                      </div>
                      <div className={`w-full h-px ${isDarkMode ? 'bg-slate-800/50' : 'bg-slate-200/80'}`}></div>
                      <div>
                        <p className={`text-[11px] mb-1 uppercase tracking-wide ${isDarkMode ? 'text-slate-500' : 'text-slate-400'}`}>Translation</p>
                        <p className={`text-lg font-medium ${isDarkMode ? 'text-emerald-300' : 'text-emerald-700'}`}>{msg.translation}</p>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>

            {/* Mic Controls */}
            <div className={`pt-4 flex flex-col items-center justify-center pb-6 border-t transition-colors duration-300 ${isDarkMode ? 'border-slate-800/60' : 'border-slate-200/60'}`}>
              <button 
                onClick={toggleRecording}
                className={`relative flex items-center justify-center w-16 h-16 rounded-full transition-all duration-300 backdrop-blur-md border ${isRecording ? (isDarkMode ? 'bg-rose-500/10 border-rose-500/30' : 'bg-rose-50 border-rose-200') : (isDarkMode ? 'bg-slate-800/60 hover:bg-slate-700 border-slate-700' : 'bg-white/80 hover:bg-white border-slate-200 shadow-sm')}`}
              >
                <div className={`w-12 h-12 rounded-full flex items-center justify-center transition-colors duration-300 ${isRecording ? 'bg-rose-500/90 text-white shadow-inner' : isDarkMode ? 'bg-slate-700 text-slate-300' : 'bg-slate-100 text-slate-600'}`}>
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                  </svg>
                </div>
              </button>
              <p className={`text-xs font-medium mt-3 ${isDarkMode ? 'text-slate-500' : 'text-slate-400'}`}>
                {isRecording ? "Listening..." : "Tap to listen"}
              </p>
            </div>
          </div>

          {/* AI Guidance Side Panel */}
          <div className={`flex flex-col rounded-2xl p-6 h-full border backdrop-blur-md transition-colors duration-300 ${isDarkMode ? 'bg-slate-900/40 border-slate-800/60' : 'bg-white/60 border-white/60 shadow-lg'}`}>
            <h2 className={`text-sm font-semibold mb-5 flex items-center gap-2 ${isDarkMode ? 'text-slate-200' : 'text-slate-800'}`}>
              <span className="flex h-2 w-2 rounded-full bg-pink-400"></span>
              AI Guidance
            </h2>
            
            <div className={`flex-1 rounded-xl p-5 border backdrop-blur-sm transition-colors duration-300 ${isDarkMode ? 'bg-slate-900/50 border-pink-900/30' : 'bg-white/80 border-pink-100 shadow-sm'}`}>
              <p className={`text-base leading-relaxed ${isDarkMode ? 'text-pink-100/90' : 'text-slate-700'}`}>
                {guidancePrompt}
              </p>
            </div>

            <div className="mt-6 flex flex-col gap-3">
              <button className={`w-full py-2.5 px-4 rounded-lg transition-colors flex justify-between items-center text-sm font-medium border ${isDarkMode ? 'bg-slate-800/50 hover:bg-slate-800 border-slate-700/50 text-slate-300' : 'bg-white/90 hover:bg-white border-slate-200/80 text-slate-700 shadow-sm'}`}>
                <span>View Profile</span>
                <span className={isDarkMode ? 'text-slate-500' : 'text-slate-400'}>→</span>
              </button>
              <button className={`w-full py-2.5 px-4 rounded-lg transition-colors flex justify-between items-center text-sm font-medium border ${isDarkMode ? 'bg-blue-500/10 hover:bg-blue-500/20 border-blue-500/20 text-blue-300' : 'bg-blue-50 hover:bg-blue-100 border-blue-100 text-blue-700 shadow-sm'}`}>
                <span>New Service Request</span>
                <span className={isDarkMode ? 'text-blue-400' : 'text-blue-500'}>→</span>
              </button>
              <button 
                onClick={() => {
                  if (ws.current && ws.current.readyState === WebSocket.OPEN) {
                    ws.current.send(JSON.stringify({action: "summarize"}));
                  }
                }}
                className={`w-full py-2.5 px-4 rounded-lg transition-colors flex justify-between items-center text-sm font-medium border ${isDarkMode ? 'bg-emerald-500/10 hover:bg-emerald-500/20 border-emerald-500/30 text-emerald-300' : 'bg-emerald-50 hover:bg-emerald-100 border-emerald-200 text-emerald-700 shadow-sm'}`}>
                <span>End & Summarize</span>
                <span>✨</span>
              </button>
            </div>

            {summary && (
              <div className={`mt-6 p-4 rounded-xl border transition-colors ${isDarkMode ? 'bg-gradient-to-br from-emerald-500/10 to-teal-500/5 border-emerald-500/30' : 'bg-emerald-50 border-emerald-200'}`}>
                <h3 className={`text-sm font-bold mb-2 ${isDarkMode ? 'text-emerald-400' : 'text-emerald-700'}`}>Interaction Summary</h3>
                <p className={`text-sm whitespace-pre-wrap ${isDarkMode ? 'text-slate-300' : 'text-slate-600'}`}>{summary}</p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}

export default App
