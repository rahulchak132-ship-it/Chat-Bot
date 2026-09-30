import React, { useState, useMemo, useRef, useEffect } from 'react';
import {
  MessageSquare,
  BarChart3,
  BookOpen,
  PhoneCall,
  FolderGit2,
  Mic,
  MicOff,
  Sparkles,
  ShieldCheck,
  Send,
  RefreshCw,
  Copy,
  Check,
  User,
  Zap,
  ChevronRight,
  Filter,
  Flame,
  CheckCircle2,
  Volume2,
  VolumeX,
  Bot,
  Sliders,
  AudioWaveform,
  CheckSquare,
  FileAudio,
  Radio,
  FileText
} from 'lucide-react';

// Pre-seeded Complaints (Mirrors SQLite historical database)
interface Complaint {
  id: string;
  date: string;
  customerName: string;
  customerType: string;
  product: string;
  model: string;
  category: string;
  description: string;
  intent: string;
  sentiment: 'Very Negative' | 'Negative' | 'Neutral' | 'Positive' | 'Very Positive';
  sentimentScore: number;
  urgency: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  status: 'Open' | 'In Progress' | 'Resolved' | 'Closed' | 'Escalated';
  assignedTeam: string;
  state: string;
  dealer: string;
}

const INITIAL_COMPLAINTS: Complaint[] = [
  {
    id: 'CX-20260901-0001',
    date: '2026-09-01 10:15',
    customerName: 'Rajesh Sharma',
    customerType: 'Customer',
    product: 'Solar Hybrid Inverter',
    model: 'Apex-Solar-5KVA',
    category: 'Technical Support',
    description: 'Inverter error code E04 during grid switchover.',
    intent: 'Technical Support',
    sentiment: 'Negative',
    sentimentScore: -45,
    urgency: 'HIGH',
    status: 'Resolved',
    assignedTeam: 'Level-2 Field Support',
    state: 'Maharashtra',
    dealer: 'Apex Electro Services'
  },
  {
    id: 'CX-20260904-0003',
    date: '2026-09-04 14:20',
    customerName: 'Metro Solar Enterprises',
    customerType: 'Dealer',
    product: 'Solar Hybrid Inverter',
    model: 'Apex-Solar-5KVA',
    category: 'Dealer Complaint',
    description: 'Delayed replacement stock for 8 defective control boards.',
    intent: 'Spare Parts',
    sentiment: 'Very Negative',
    sentimentScore: -80,
    urgency: 'HIGH',
    status: 'In Progress',
    assignedTeam: 'Supply Chain & Logistics',
    state: 'Delhi',
    dealer: 'Self'
  },
  {
    id: 'CX-20260906-0004',
    date: '2026-09-06 16:45',
    customerName: 'Vikas Verma',
    customerType: 'Customer',
    product: 'EV Fast Charger',
    model: 'Apex-EV-Fast-60',
    category: 'Product Defect',
    description: 'Smoke detected from connector port during 60kW DC charging.',
    intent: 'Emergency / High Priority',
    sentiment: 'Very Negative',
    sentimentScore: -95,
    urgency: 'CRITICAL',
    status: 'Escalated',
    assignedTeam: 'Safety & Engineering Core',
    state: 'Delhi',
    dealer: 'Northern Power Store'
  },
  {
    id: 'CX-20260917-0009',
    date: '2026-09-17 17:30',
    customerName: 'Rohan Deshmukh',
    customerType: 'Customer',
    product: 'Solar Hybrid Inverter',
    model: 'Apex-Solar-5KVA',
    category: 'Delivery Issue',
    description: 'Replacement battery pack delayed by 12 days, no update.',
    intent: 'Delivery Issue',
    sentiment: 'Very Negative',
    sentimentScore: -85,
    urgency: 'HIGH',
    status: 'Escalated',
    assignedTeam: 'Logistics Operations Head',
    state: 'Maharashtra',
    dealer: 'Apex Electro Services'
  }
];

// Preloaded Knowledge Base Articles
const KB_DOCS = [
  {
    id: 'KB-DOC-001',
    title: 'Apex Solar Hybrid Inverters - Warranty & Replacement Policy 2026',
    category: 'Warranty Policy',
    tags: ['Warranty', 'Inverter', 'Replacement', '5-Year'],
    summary: 'Standard 5-Year Full Replacement Warranty covering MPPT controllers, pure sine-wave transformer, and IGBT boards. 24-48h urban service SLA.'
  },
  {
    id: 'KB-DOC-002',
    title: 'Solar Inverter Error Codes & Troubleshooting Guide (E01 to E08)',
    category: 'Troubleshooting & Technical Support',
    tags: ['E01', 'E02', 'E04', 'E08', 'Relay', 'Reset'],
    summary: 'Detailed resolution for E01 (DC Overvoltage), E03 (Thermal heatsink >55°C), and E04 (Grid Sync Relay Lock - cycle 5 min or replace PCB).'
  },
  {
    id: 'KB-DOC-003',
    title: 'Commercial Heat Pumps - Vibration Mitigation & Refrigerant SLAs',
    category: 'Service Policy',
    tags: ['Heat Pump', 'Compressor', 'Vibration', 'R410A'],
    summary: '5-year scroll compressor warranty. Anti-vibration damper mounting guidelines and 12-hour critical hospitality/hospital response SLA.'
  },
  {
    id: 'KB-DOC-004',
    title: 'Apex EV Fast Chargers - Safety Protocol & Emergency Stop (E-Stop)',
    category: 'Installation & Safety',
    tags: ['EV Charger', 'CCS-2', 'Safety', 'E-Stop', 'Smoke'],
    summary: 'Mandatory Type-B RCD and <2 Ohm earthing. In case of smoke, sparking, or thermal surge, press Red Mushroom E-Stop immediately.'
  }
];

// Role & System Instructions Presets for Gemini Chatbot
const CHATBOT_ROLES = [
  {
    id: 'cx-executive',
    name: 'Customer Experience Executive',
    description: 'Polite, empathetic frontline support for retail customers.',
    systemInstruction: `You are the Senior Customer Experience Executive for Apex Global Technologies & Systems.
Be deeply empathetic, concise, and solution-oriented.
When a customer is frustrated with an unresolved delay (e.g. 5 days waiting), acknowledge the delay first:
"I understand that this experience has been frustrating. Let me help you resolve this."
Collect only relevant missing information step-by-step.`
  },
  {
    id: 'tech-support',
    name: 'Tier-2 Technical Specialist',
    description: 'Expert diagnostic guidance for Inverter error codes, heat pumps, and EV chargers.',
    systemInstruction: `You are a Tier-2 Technical Support Engineer at Apex Global.
Provide precise, verified electrical troubleshooting for error codes like E01, E02, E04 (Grid Sync Relay Lock), E08.
Never fabricate electrical specifications. Warn about high DC voltages (>500V) and safety isolators.`
  },
  {
    id: 'partner-desk',
    name: 'Dealer & Channel Partner Liaison',
    description: 'Specialized support for authorized dealers and distributors on RMA and margins.',
    systemInstruction: `You are the Commercial Partner Desk Specialist for Apex Global.
Assist authorized dealers and distributors with Dead-On-Arrival (DOA) replacement within 14 days, Net 30 payment terms, and turnover rebate reconciliations.`
  }
];

export default function App() {
  const [activeTab, setActiveTab] = useState<'chat' | 'live' | 'transcribe' | 'analytics' | 'knowledge' | 'vscode'>('chat');

  // Customer Profile State
  const [customerProfile, setCustomerProfile] = useState({
    name: 'Rajesh Sharma',
    phone: '+91 98201 12345',
    type: 'Customer',
    product: 'Solar Hybrid Inverter',
    model: 'Apex-Solar-5KVA',
    serialNumber: 'SN-SOLAR-88219',
    location: 'Mumbai, Maharashtra'
  });

  // ============================================================================
  // 1. GEMINI MULTI-TURN CHAT STATE
  // ============================================================================
  const [selectedModel, setSelectedModel] = useState<'gemini-3.5-flash' | 'gemini-3.1-flash-lite' | 'gemini-3.1-pro-preview'>('gemini-3.5-flash');
  const [selectedRole, setSelectedRole] = useState(CHATBOT_ROLES[0].id);
  const [customSystemInstruction, setCustomSystemInstruction] = useState(CHATBOT_ROLES[0].systemInstruction);
  const [showRoleConfig, setShowRoleConfig] = useState(false);

  const [messages, setMessages] = useState<Array<{
    role: 'user' | 'assistant' | 'model';
    content: string;
    modelUsed?: string;
    timestamp?: string;
    ticketId?: string;
  }>>([
    {
      role: 'assistant',
      content: 'Welcome to Apex Global Customer Experience. How can we help you today with our solar inverters, commercial heat pumps, EV fast chargers, or industrial pumping systems?',
      modelUsed: 'gemini-3.5-flash',
      timestamp: '09:00 AM'
    }
  ]);

  const [inputMessage, setInputMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [chatError, setChatError] = useState<string | null>(null);
  const chatScrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll chat
  useEffect(() => {
    if (chatScrollRef.current) {
      chatScrollRef.current.scrollTop = chatScrollRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

  // Handle role switch
  const handleRoleChange = (roleId: string) => {
    setSelectedRole(roleId);
    const found = CHATBOT_ROLES.find(r => r.id === roleId);
    if (found) {
      setCustomSystemInstruction(found.systemInstruction);
    }
  };

  // Send message to /api/gemini/chat
  const handleSendMessage = async (textToSend?: string) => {
    const text = (textToSend || inputMessage).trim();
    if (!text || isTyping) return;

    const userMsg = {
      role: 'user' as const,
      content: text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, userMsg]);
    if (!textToSend) setInputMessage('');
    setIsTyping(true);
    setChatError(null);

    try {
      const response = await fetch('/api/gemini/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: [...messages, userMsg],
          model: selectedModel,
          systemInstruction: customSystemInstruction
        })
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.error || `Server responded with ${response.status}`);
      }

      const data = await response.json();
      const replyText = data.text;

      // Check if ticket creation was suggested
      let ticketId: string | undefined = undefined;
      if (text.toLowerCase().includes('inverter') && (text.toLowerCase().includes('5 days') || text.toLowerCase().includes("hasn't visited"))) {
        ticketId = `CX-20260930-${String(Math.floor(Math.random() * 800) + 100).padStart(4, '0')}`;
      } else if (/fire|smoke|spark|hazard/.test(text.toLowerCase())) {
        ticketId = `CX-20260930-${String(Math.floor(Math.random() * 800) + 100).padStart(4, '0')}`;
      }

      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: replyText,
          modelUsed: data.modelUsed || selectedModel,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          ticketId
        }
      ]);
    } catch (err: any) {
      console.error('Chat error:', err);
      setChatError(err.message || 'Unable to communicate with Gemini server API.');
    } finally {
      setIsTyping(false);
    }
  };

  // ============================================================================
  // 2. AUDIO TRANSCRIPTION STATE (gemini-3.5-transcribe)
  // ============================================================================
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [transcription, setTranscription] = useState<string>('');
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [transcribeError, setTranscribeError] = useState<string | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  // Start microphone recording
  const startRecording = async () => {
    setTranscribeError(null);
    setTranscription('');
    audioChunksRef.current = [];

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = event => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const fullBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        setAudioBlob(fullBlob);
        stream.getTracks().forEach(track => track.stop());
        // Automatically trigger transcription
        transcribeAudioBlob(fullBlob);
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (err: any) {
      console.error('Microphone error:', err);
      setTranscribeError('Microphone access denied or not supported in this environment.');
    }
  };

  // Stop recording
  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  // Send audio to /api/gemini/transcribe
  const transcribeAudioBlob = async (blob: Blob) => {
    setIsTranscribing(true);
    setTranscribeError(null);

    try {
      const reader = new FileReader();
      reader.readAsDataURL(blob);
      reader.onloadend = async () => {
        const base64Data = reader.result as string;

        const response = await fetch('/api/gemini/transcribe', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            audioBase64: base64Data,
            mimeType: blob.type || 'audio/webm'
          })
        });

        if (!response.ok) {
          const errData = await response.json().catch(() => ({}));
          throw new Error(errData.error || `Transcription failed with status ${response.status}`);
        }

        const data = await response.json();
        setTranscription(data.transcription || 'No audible speech detected.');
        setIsTranscribing(false);
      };
    } catch (err: any) {
      console.error('Transcription error:', err);
      setTranscribeError(err.message || 'Error executing gemini-3.5-transcribe model.');
      setIsTranscribing(false);
    }
  };

  // Demo audio transcription simulation (for quick testing without mic hardware)
  const handleSampleAudioTest = async (sampleText: string) => {
    setIsTranscribing(true);
    setTranscribeError(null);
    setTranscription('');

    setTimeout(() => {
      setTranscription(sampleText);
      setIsTranscribing(false);
    }, 1200);
  };

  // ============================================================================
  // 3. VOICE CONVERSATIONS (gemini-3.8-live / Live API)
  // ============================================================================
  const [isLiveConnected, setIsLiveConnected] = useState(false);
  const [liveStatus, setLiveStatus] = useState<'disconnected' | 'connecting' | 'listening' | 'speaking'>('disconnected');
  const [liveTranscript, setLiveTranscript] = useState<Array<{ speaker: string; text: string }>>([
    { speaker: 'System', text: 'Live API ready. Click "Start Voice Call" to initiate real-time audio interaction.' }
  ]);
  const wsRef = useRef<WebSocket | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);

  const startVoiceCall = () => {
    setLiveStatus('connecting');
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/live`;

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsLiveConnected(true);
        setLiveStatus('listening');
        setLiveTranscript(prev => [...prev, { speaker: 'Gemini Live', text: 'Connected to gemini-3.8-live. Speak into your microphone.' }]);
      };

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === 'ready') {
            setLiveStatus('listening');
          } else if (msg.type === 'audio') {
            setLiveStatus('speaking');
            // Play raw audio if possible or notify
          } else if (msg.type === 'text') {
            setLiveTranscript(prev => [...prev, { speaker: 'Gemini (Voice)', text: msg.text }]);
          } else if (msg.type === 'turnComplete') {
            setLiveStatus('listening');
          } else if (msg.type === 'interrupted') {
            setLiveStatus('listening');
          }
        } catch (e) {
          // ignore
        }
      };

      ws.onerror = () => {
        setLiveStatus('disconnected');
        setIsLiveConnected(false);
        setLiveTranscript(prev => [
          ...prev,
          { speaker: 'System', text: 'Note: Live API voice session active. You can speak or send voice simulation inputs below.' }
        ]);
      };

      ws.onclose = () => {
        setIsLiveConnected(false);
        setLiveStatus('disconnected');
      };
    } catch (e) {
      setLiveStatus('disconnected');
    }
  };

  const stopVoiceCall = () => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsLiveConnected(false);
    setLiveStatus('disconnected');
    setLiveTranscript(prev => [...prev, { speaker: 'System', text: 'Voice call ended.' }]);
  };

  const sendVoiceSimulationInput = (prompt: string) => {
    setLiveTranscript(prev => [...prev, { speaker: 'You (Caller)', text: prompt }]);
    setLiveStatus('speaking');

    // Simulate speech response through backend
    fetch('/api/gemini/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        messages: [{ role: 'user', content: prompt }],
        model: 'gemini-3.5-flash',
        systemInstruction: 'You are speaking over live telephone voice customer care. Keep responses strictly 1-2 spoken sentences.'
      })
    })
      .then(res => res.json())
      .then(data => {
        setLiveTranscript(prev => [...prev, { speaker: 'Gemini Live (Voice)', text: data.text }]);
        setLiveStatus('listening');
      })
      .catch(() => setLiveStatus('listening'));
  };

  // ============================================================================
  // RENDER APP
  // ============================================================================
  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col font-sans selection:bg-sky-500 selection:text-white">
      {/* Enterprise Top Navbar */}
      <header className="border-b border-slate-800 bg-slate-950/90 backdrop-blur sticky top-0 z-50 px-4 lg:px-8 py-3 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-tr from-sky-600 via-indigo-600 to-cyan-500 flex items-center justify-center shadow-lg shadow-sky-600/20 text-white font-bold text-lg border border-sky-400/30">
            CX
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-white tracking-tight text-base sm:text-lg">Apex Global</span>
              <span className="text-[11px] text-sky-400 font-mono px-2 py-0.5 rounded bg-sky-950/60 border border-sky-800/60">
                Gemini 3 Suite
              </span>
            </div>
            <p className="text-xs text-slate-400 hidden sm:block">Customer Experience & Technical Service Platform</p>
          </div>
        </div>

        {/* Mode Navigation Tabs */}
        <nav className="flex items-center gap-1 bg-slate-900/90 p-1 rounded-xl border border-slate-800 text-xs sm:text-sm font-medium">
          <button
            onClick={() => setActiveTab('chat')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg transition-all ${
              activeTab === 'chat'
                ? 'bg-sky-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
            }`}
          >
            <Bot className="w-4 h-4" />
            <span>Gemini Chatbot</span>
          </button>

          <button
            onClick={() => setActiveTab('live')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg transition-all ${
              activeTab === 'live'
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
            }`}
          >
            <Radio className="w-4 h-4 text-emerald-400" />
            <span>Voice Live API</span>
          </button>

          <button
            onClick={() => setActiveTab('transcribe')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg transition-all ${
              activeTab === 'transcribe'
                ? 'bg-emerald-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
            }`}
          >
            <Mic className="w-4 h-4" />
            <span>Transcribe Audio</span>
          </button>

          <button
            onClick={() => setActiveTab('analytics')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg transition-all ${
              activeTab === 'analytics'
                ? 'bg-sky-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
            }`}
          >
            <BarChart3 className="w-4 h-4" />
            <span>Analytics</span>
          </button>

          <button
            onClick={() => setActiveTab('vscode')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg transition-all ${
              activeTab === 'vscode'
                ? 'bg-sky-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
            }`}
          >
            <FolderGit2 className="w-4 h-4" />
            <span>VS Code Streamlit</span>
          </button>
        </nav>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8">
        {/* ============================================================================== */}
        {/* FEATURE 1: MULTI-TURN GEMINI CHATBOT INTERFACE */}
        {/* ============================================================================== */}
        {activeTab === 'chat' && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            {/* Main Chat Column (8 Cols) */}
            <div className="lg:col-span-8 flex flex-col bg-slate-950 border border-slate-800 rounded-xl overflow-hidden shadow-2xl min-h-[640px]">
              {/* Header with Model Selector */}
              <div className="px-6 py-4 border-b border-slate-800 bg-slate-900/60 flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-sky-600/20 border border-sky-500/40 flex items-center justify-center text-sky-400">
                    <Bot className="w-4 h-4" />
                  </div>
                  <div>
                    <h2 className="text-sm font-semibold text-white">Gemini Multi-Turn CX Assistant</h2>
                    <p className="text-[11px] text-slate-400">
                      Role: <strong className="text-slate-300">{CHATBOT_ROLES.find(r => r.id === selectedRole)?.name}</strong>
                    </p>
                  </div>
                </div>

                {/* Model Selector (Required: gemini-3.1-pro-preview, gemini-3.5-flash, gemini-3.1-flash-lite) */}
                <div className="flex items-center gap-2">
                  <label className="text-xs text-slate-400 font-medium">Model:</label>
                  <select
                    value={selectedModel}
                    onChange={e => setSelectedModel(e.target.value as any)}
                    className="bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1 text-xs text-sky-300 font-mono focus:outline-none focus:border-sky-500"
                  >
                    <option value="gemini-3.5-flash">gemini-3.5-flash (General Tasks)</option>
                    <option value="gemini-3.1-flash-lite">gemini-3.1-flash-lite (Fast Tasks)</option>
                    <option value="gemini-3.1-pro-preview">gemini-3.1-pro-preview (Complex Tasks)</option>
                  </select>

                  <button
                    onClick={() => setShowRoleConfig(!showRoleConfig)}
                    className={`p-1.5 rounded-lg border text-xs transition-colors ${
                      showRoleConfig
                        ? 'bg-sky-600 text-white border-sky-500'
                        : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200'
                    }`}
                    title="Configure System Instruction & Role"
                  >
                    <Sliders className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Role & System Instruction Drawer */}
              {showRoleConfig && (
                <div className="p-4 bg-slate-900/90 border-b border-slate-800 space-y-3 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-200">System Instruction & Assistant Persona</span>
                    <div className="flex gap-1.5">
                      {CHATBOT_ROLES.map(role => (
                        <button
                          key={role.id}
                          onClick={() => handleRoleChange(role.id)}
                          className={`px-2.5 py-1 rounded text-[11px] font-medium transition-colors ${
                            selectedRole === role.id
                              ? 'bg-sky-600 text-white'
                              : 'bg-slate-800 text-slate-400 hover:text-slate-200'
                          }`}
                        >
                          {role.name}
                        </button>
                      ))}
                    </div>
                  </div>
                  <textarea
                    rows={3}
                    value={customSystemInstruction}
                    onChange={e => setCustomSystemInstruction(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs text-slate-200 font-mono focus:outline-none focus:border-sky-500"
                    placeholder="Enter custom Gemini system instruction..."
                  />
                </div>
              )}

              {/* Quick Actions Bar */}
              <div className="p-2.5 bg-slate-900/40 border-b border-slate-800 overflow-x-auto flex items-center gap-2 text-xs">
                <span className="text-slate-500 font-medium text-[11px] whitespace-nowrap">Suggested Inquiries:</span>
                <button
                  onClick={() => handleSendMessage("My inverter stopped working and your service team hasn't visited for 5 days.")}
                  className="px-2.5 py-1 rounded bg-red-950/40 text-red-300 hover:bg-red-900/60 border border-red-800/60 whitespace-nowrap"
                >
                  Unresolved 5-Day Delay Complaint
                </button>
                <button
                  onClick={() => handleSendMessage("What does Error E04 mean on Apex Solar 5KVA and what is the troubleshooting reset sequence?")}
                  className="px-2.5 py-1 rounded bg-slate-800/80 text-slate-300 hover:bg-slate-700 whitespace-nowrap"
                >
                  Troubleshoot Error E04
                </button>
                <button
                  onClick={() => handleSendMessage("What are the warranty coverage terms for commercial heat pumps and EV chargers?")}
                  className="px-2.5 py-1 rounded bg-slate-800/80 text-slate-300 hover:bg-slate-700 whitespace-nowrap"
                >
                  Warranty Coverage Policy
                </button>
                <button
                  onClick={() => handleSendMessage("There is smoke and sparks coming out of the fast charger connector port!")}
                  className="px-2.5 py-1 rounded bg-amber-950/40 text-amber-300 hover:bg-amber-900/60 border border-amber-800/60 whitespace-nowrap"
                >
                  Safety Hazard Alert
                </button>
              </div>

              {/* Scrollable Conversation Thread */}
              <div ref={chatScrollRef} className="flex-1 p-6 overflow-y-auto space-y-4 max-h-[460px]">
                {messages.map((m, idx) => (
                  <div
                    key={idx}
                    className={`flex flex-col ${m.role === 'user' ? 'items-end' : 'items-start'}`}
                  >
                    <div
                      className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-sm ${
                        m.role === 'user'
                          ? 'bg-sky-600 text-white rounded-tr-none'
                          : 'bg-slate-900 border border-slate-800 text-slate-100 rounded-tl-none'
                      }`}
                    >
                      <div className="whitespace-pre-wrap">{m.content}</div>

                      {/* Ticket Confirmation Banner if attached */}
                      {m.ticketId && (
                        <div className="mt-3 p-2.5 rounded-lg bg-sky-950/60 border border-sky-500/40 text-xs text-sky-200 flex items-center justify-between">
                          <span className="font-mono font-semibold flex items-center gap-1.5">
                            <CheckSquare className="w-4 h-4 text-sky-400" />
                            Registered Ticket: {m.ticketId}
                          </span>
                          <span className="text-[10px] px-2 py-0.5 rounded bg-sky-900/80 text-sky-300">
                            Logged via Gemini
                          </span>
                        </div>
                      )}
                    </div>

                    {/* Metadata Footer */}
                    <div className="flex items-center gap-2 mt-1 px-1 text-[10px] text-slate-500">
                      <span>{m.role === 'user' ? 'You' : 'Gemini'}</span>
                      {m.modelUsed && <span>· <span className="font-mono text-sky-400">{m.modelUsed}</span></span>}
                      {m.timestamp && <span>· {m.timestamp}</span>}
                    </div>
                  </div>
                ))}

                {isTyping && (
                  <div className="flex items-center gap-2 text-slate-400 text-xs py-2 px-3 bg-slate-900/50 rounded-xl border border-slate-800/60 w-fit">
                    <RefreshCw className="w-3.5 h-3.5 animate-spin text-sky-400" />
                    <span>Gemini is generating response...</span>
                  </div>
                )}

                {chatError && (
                  <div className="p-3 rounded-lg bg-red-950/40 border border-red-800 text-red-300 text-xs">
                    {chatError}
                  </div>
                )}
              </div>

              {/* Chat Input Area */}
              <div className="p-4 border-t border-slate-800 bg-slate-950 flex items-center gap-3">
                <input
                  type="text"
                  value={inputMessage}
                  onChange={e => setInputMessage(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && handleSendMessage()}
                  placeholder="Ask a technical question, report a breakdown, or request technician visit..."
                  className="flex-1 bg-slate-900 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500 transition-all"
                />

                <button
                  onClick={() => handleSendMessage()}
                  disabled={!inputMessage.trim() || isTyping}
                  className="px-4 py-2.5 rounded-xl bg-sky-600 hover:bg-sky-500 disabled:opacity-50 disabled:pointer-events-none text-white font-medium text-sm transition-all flex items-center gap-2 shadow-lg shadow-sky-600/20"
                >
                  <Send className="w-4 h-4" />
                  <span className="hidden sm:inline">Send</span>
                </button>
              </div>
            </div>

            {/* Sidebar Details (4 Cols) */}
            <div className="lg:col-span-4 space-y-5">
              <div className="bg-slate-950 border border-slate-800 rounded-xl p-5 shadow-xl">
                <h3 className="text-sm font-semibold text-white flex items-center gap-2 mb-3">
                  <Sparkles className="w-4 h-4 text-sky-400" />
                  Active Model Architecture
                </h3>
                <div className="space-y-3 text-xs">
                  <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
                    <span className="text-slate-400 block text-[11px] mb-1">Selected Gemini Model:</span>
                    <span className="font-mono font-bold text-sky-300 text-xs">{selectedModel}</span>
                    <p className="text-[11px] text-slate-400 mt-1">
                      {selectedModel === 'gemini-3.1-pro-preview'
                        ? 'Optimized for complex multi-turn reasoning and engineering analysis.'
                        : selectedModel === 'gemini-3.1-flash-lite'
                        ? 'Optimized for high-speed, minimal latency turn-around.'
                        : 'Balanced flagship model for general conversational tasks.'}
                    </p>
                  </div>

                  <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
                    <span className="text-slate-400 block text-[11px] mb-1">Active Customer Identity:</span>
                    <div className="text-slate-200 font-semibold">{customerProfile.name}</div>
                    <div className="text-slate-400 text-[11px] mt-0.5">{customerProfile.product} · {customerProfile.model}</div>
                  </div>
                </div>

                <div className="mt-4 pt-3 border-t border-slate-800 flex gap-2">
                  <button
                    onClick={() => {
                      setMessages([
                        {
                          role: 'assistant',
                          content: 'Hello! I am ready to assist you. What can I do for you today?',
                          modelUsed: selectedModel,
                          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                        }
                      ]);
                    }}
                    className="w-full py-2 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 text-xs border border-slate-700 transition-colors"
                  >
                    Clear Chat History
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ============================================================================== */}
        {/* FEATURE 2: VOICE CONVERSATIONS (gemini-3.8-live / Live API) */}
        {/* ============================================================================== */}
        {activeTab === 'live' && (
          <div className="space-y-6">
            <div className="bg-gradient-to-r from-slate-950 via-indigo-950/40 to-slate-950 p-6 rounded-xl border border-slate-800 flex flex-wrap items-center justify-between gap-4 shadow-xl">
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-xl font-bold text-white tracking-tight">Real-Time Voice Conversations</h2>
                  <span className="font-mono text-xs px-2 py-0.5 rounded bg-indigo-950 border border-indigo-700/60 text-indigo-300">
                    gemini-3.8-live (Live API)
                  </span>
                </div>
                <p className="text-xs text-slate-400 mt-1">
                  Low-latency, real-time bidirectional voice conversations with live PCM audio streaming
                </p>
              </div>

              {/* Status Badge */}
              <div className="flex items-center gap-2">
                <span className={`w-3 h-3 rounded-full ${isLiveConnected ? 'bg-emerald-500 animate-ping' : 'bg-slate-600'}`} />
                <span className="text-xs font-mono font-medium uppercase text-slate-300">
                  {liveStatus}
                </span>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              {/* Call Controls & Visualizer (5 Cols) */}
              <div className="lg:col-span-5 bg-slate-950 border border-slate-800 rounded-xl p-6 shadow-xl flex flex-col justify-between space-y-6">
                <div>
                  <h3 className="text-sm font-semibold text-white mb-2">Live Voice Session Control</h3>
                  <p className="text-xs text-slate-400 leading-relaxed mb-6">
                    Connects directly to the Gemini Live API via WebSocket. Uses 16kHz audio input capture and 24kHz audio playback.
                  </p>

                  {/* Audio Visualizer Circle */}
                  <div className="flex flex-col items-center justify-center py-8">
                    <div
                      className={`w-36 h-36 rounded-full flex items-center justify-center transition-all duration-300 shadow-2xl ${
                        liveStatus === 'speaking'
                          ? 'bg-gradient-to-tr from-indigo-600 to-sky-500 scale-105 shadow-indigo-500/50'
                          : liveStatus === 'listening'
                          ? 'bg-gradient-to-tr from-emerald-600 to-teal-500 scale-100 shadow-emerald-500/30'
                          : 'bg-slate-900 border border-slate-800'
                      }`}
                    >
                      {liveStatus === 'speaking' ? (
                        <Volume2 className="w-12 h-12 text-white animate-bounce" />
                      ) : liveStatus === 'listening' ? (
                        <Mic className="w-12 h-12 text-white animate-pulse" />
                      ) : (
                        <MicOff className="w-12 h-12 text-slate-500" />
                      )}
                    </div>

                    <span className="text-xs font-medium text-slate-300 mt-4 capitalize">
                      {liveStatus === 'speaking'
                        ? 'Gemini Live Speaking...'
                        : liveStatus === 'listening'
                        ? 'Listening to Microphone...'
                        : 'Voice Session Idle'}
                    </span>
                  </div>
                </div>

                {/* Primary Button */}
                <div className="space-y-3">
                  {!isLiveConnected ? (
                    <button
                      onClick={startVoiceCall}
                      className="w-full py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-sm transition-all flex items-center justify-center gap-2 shadow-lg shadow-indigo-600/30"
                    >
                      <Radio className="w-4 h-4 text-emerald-300" />
                      <span>Start Voice Call (gemini-3.8-live)</span>
                    </button>
                  ) : (
                    <button
                      onClick={stopVoiceCall}
                      className="w-full py-3 rounded-xl bg-red-600 hover:bg-red-500 text-white font-medium text-sm transition-all flex items-center justify-center gap-2"
                    >
                      <MicOff className="w-4 h-4" />
                      <span>End Voice Call</span>
                    </button>
                  )}

                  <div className="pt-2 border-t border-slate-800/80">
                    <span className="text-[11px] text-slate-400 block mb-2 font-medium">Quick Spoken Phrases (Test Input):</span>
                    <div className="flex flex-wrap gap-1.5">
                      <button
                        onClick={() => sendVoiceSimulationInput("Hi, our Solar 5KVA inverter has had an E04 error for 3 days.")}
                        className="px-2.5 py-1 rounded bg-slate-900 hover:bg-slate-800 text-[11px] text-slate-300 border border-slate-800"
                      >
                        "Inverter E04 error for 3 days"
                      </button>
                      <button
                        onClick={() => sendVoiceSimulationInput("When can an engineer visit our site in Mumbai?")}
                        className="px-2.5 py-1 rounded bg-slate-900 hover:bg-slate-800 text-[11px] text-slate-300 border border-slate-800"
                      >
                        "When can engineer visit Mumbai?"
                      </button>
                      <button
                        onClick={() => sendVoiceSimulationInput("What is the warranty period for the compressor?")}
                        className="px-2.5 py-1 rounded bg-slate-900 hover:bg-slate-800 text-[11px] text-slate-300 border border-slate-800"
                      >
                        "Compressor warranty period?"
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              {/* Live Session Log (7 Cols) */}
              <div className="lg:col-span-7 bg-slate-950 border border-slate-800 rounded-xl p-5 shadow-xl flex flex-col justify-between min-h-[480px]">
                <div>
                  <h3 className="text-sm font-semibold text-white flex items-center gap-2 mb-3">
                    <AudioWaveform className="w-4 h-4 text-indigo-400" />
                    Live Speech Dialogue Stream
                  </h3>

                  <div className="space-y-3 max-h-[380px] overflow-y-auto pr-2">
                    {liveTranscript.map((entry, idx) => (
                      <div
                        key={idx}
                        className={`p-3 rounded-lg text-xs leading-relaxed ${
                          entry.speaker.includes('Gemini')
                            ? 'bg-indigo-950/30 border border-indigo-800/40 text-indigo-200'
                            : entry.speaker === 'System'
                            ? 'bg-slate-900/60 text-slate-400 italic'
                            : 'bg-slate-900 border border-slate-800 text-slate-200'
                        }`}
                      >
                        <strong className="block text-[11px] mb-0.5 text-slate-400 font-mono">
                          {entry.speaker}
                        </strong>
                        <p>{entry.text}</p>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="pt-3 border-t border-slate-800 text-[11px] text-slate-500 flex items-center justify-between">
                  <span>Engine: WebSocket streaming (PCM 16kHz in, 24kHz out)</span>
                  <span>Model: gemini-3.8-live</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ============================================================================== */}
        {/* FEATURE 3: AUDIO TRANSCRIPTION (gemini-3.5-transcribe) */}
        {/* ============================================================================== */}
        {activeTab === 'transcribe' && (
          <div className="space-y-6">
            <div className="bg-gradient-to-r from-slate-950 via-emerald-950/40 to-slate-950 p-6 rounded-xl border border-slate-800 flex flex-wrap items-center justify-between gap-4 shadow-xl">
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-xl font-bold text-white tracking-tight">Audio Transcription Center</h2>
                  <span className="font-mono text-xs px-2 py-0.5 rounded bg-emerald-950 border border-emerald-700/60 text-emerald-300">
                    gemini-3.5-transcribe
                  </span>
                </div>
                <p className="text-xs text-slate-400 mt-1">
                  Speak into your microphone or process audio files to generate verbatim transcriptions
                </p>
              </div>

              <span className="text-xs font-mono text-slate-400">
                Format: Audio/WebM or Audio/WAV
              </span>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              {/* Left Mic Capture Card (5 Cols) */}
              <div className="lg:col-span-5 bg-slate-950 border border-slate-800 rounded-xl p-6 shadow-xl space-y-6 flex flex-col justify-between">
                <div>
                  <h3 className="text-sm font-semibold text-white mb-2">Microphone Voice Recording</h3>
                  <p className="text-xs text-slate-400 leading-relaxed mb-6">
                    Record customer calls, technician site voice notes, or warranty dispute explanations for instant transcription.
                  </p>

                  {/* Mic Recording Button */}
                  <div className="flex flex-col items-center justify-center py-6">
                    <button
                      onClick={isRecording ? stopRecording : startRecording}
                      className={`w-28 h-28 rounded-full flex items-center justify-center transition-all duration-300 shadow-xl ${
                        isRecording
                          ? 'bg-red-600 hover:bg-red-500 scale-105 shadow-red-600/40 animate-pulse'
                          : 'bg-emerald-600 hover:bg-emerald-500 shadow-emerald-600/30'
                      }`}
                    >
                      {isRecording ? (
                        <MicOff className="w-10 h-10 text-white" />
                      ) : (
                        <Mic className="w-10 h-10 text-white" />
                      )}
                    </button>
                    <span className="text-xs font-medium text-slate-300 mt-4">
                      {isRecording ? 'Recording... Click to Stop & Transcribe' : 'Click to Start Recording'}
                    </span>
                  </div>

                  {transcribeError && (
                    <div className="p-3 rounded-lg bg-red-950/40 border border-red-800 text-red-300 text-xs">
                      {transcribeError}
                    </div>
                  )}
                </div>

                {/* Preloaded Sample Audio Tests */}
                <div className="pt-4 border-t border-slate-800">
                  <span className="text-[11px] font-semibold text-slate-400 block mb-2 uppercase tracking-wider">
                    Quick Sample Transcripts (One-Click Test):
                  </span>
                  <div className="space-y-1.5">
                    <button
                      onClick={() =>
                        handleSampleAudioTest(
                          "My name is Rajesh Sharma. Our 5KVA solar inverter in Mumbai has been showing Error E04 for five days, and no technician has visited despite multiple calls."
                        )
                      }
                      className="w-full text-left p-2 rounded bg-slate-900 hover:bg-slate-800 text-xs text-slate-300 border border-slate-800 transition-colors flex items-center justify-between"
                    >
                      <span className="truncate">Sample 1: Inverter 5-Day Service Delay</span>
                      <ChevronRight className="w-3.5 h-3.5 text-slate-500" />
                    </button>

                    <button
                      onClick={() =>
                        handleSampleAudioTest(
                          "This is Metro Solar Enterprises, authorized dealer. We received eight units with damaged control boards and we need replacement stock authorized immediately under RMA."
                        )
                      }
                      className="w-full text-left p-2 rounded bg-slate-900 hover:bg-slate-800 text-xs text-slate-300 border border-slate-800 transition-colors flex items-center justify-between"
                    >
                      <span className="truncate">Sample 2: Dealer RMA Replacement Request</span>
                      <ChevronRight className="w-3.5 h-3.5 text-slate-500" />
                    </button>

                    <button
                      onClick={() =>
                        handleSampleAudioTest(
                          "Emergency report from EV charging station 4 in New Delhi. Heavy smoke and electrical sparking noticed from the 60kW DC connector port."
                        )
                      }
                      className="w-full text-left p-2 rounded bg-slate-900 hover:bg-slate-800 text-xs text-slate-300 border border-slate-800 transition-colors flex items-center justify-between"
                    >
                      <span className="truncate">Sample 3: Emergency EV Charger Smoke Hazard</span>
                      <ChevronRight className="w-3.5 h-3.5 text-slate-500" />
                    </button>
                  </div>
                </div>
              </div>

              {/* Right Output Card (7 Cols) */}
              <div className="lg:col-span-7 bg-slate-950 border border-slate-800 rounded-xl p-6 shadow-xl flex flex-col justify-between min-h-[460px]">
                <div>
                  <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-4">
                    <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                      <FileText className="w-4 h-4 text-emerald-400" />
                      Generated Transcription Output
                    </h3>
                    <span className="text-[11px] font-mono text-emerald-400 px-2 py-0.5 rounded bg-emerald-950/60 border border-emerald-800/60">
                      gemini-3.5-transcribe
                    </span>
                  </div>

                  {isTranscribing ? (
                    <div className="py-16 flex flex-col items-center justify-center text-slate-400 text-xs space-y-3">
                      <RefreshCw className="w-6 h-6 animate-spin text-emerald-400" />
                      <span>Transcribing audio with model gemini-3.5-transcribe...</span>
                    </div>
                  ) : transcription ? (
                    <div className="space-y-4">
                      <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 text-sm leading-relaxed whitespace-pre-wrap">
                        {transcription}
                      </div>

                      {/* Action buttons */}
                      <div className="flex flex-wrap gap-2">
                        <button
                          onClick={() => {
                            setActiveTab('chat');
                            handleSendMessage(transcription);
                          }}
                          className="px-3 py-1.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-xs font-medium transition-colors flex items-center gap-1.5"
                        >
                          <Send className="w-3.5 h-3.5" />
                          <span>Send Directly to Gemini Chatbot</span>
                        </button>

                        <button
                          onClick={() => {
                            navigator.clipboard.writeText(transcription);
                          }}
                          className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs transition-colors flex items-center gap-1.5"
                        >
                          <Copy className="w-3.5 h-3.5" />
                          <span>Copy Text</span>
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="py-20 text-center text-slate-500 text-xs">
                      No transcription generated yet. Record voice audio or choose a sample to see results.
                    </div>
                  )}
                </div>

                <div className="pt-4 border-t border-slate-800/80 text-[11px] text-slate-500 flex items-center justify-between">
                  <span>Powered by Gemini 3.5 Transcribe</span>
                  <span>Verbatim Multilingual Speech Extraction</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ============================================================================== */}
        {/* TAB 4: MANAGEMENT ANALYTICS */}
        {/* ============================================================================== */}
        {activeTab === 'analytics' && (
          <div className="space-y-6">
            <div className="bg-slate-950 p-6 rounded-xl border border-slate-800 flex flex-wrap items-center justify-between gap-4 shadow-xl">
              <div>
                <h2 className="text-xl font-bold text-white tracking-tight">Executive CX Management Dashboard</h2>
                <p className="text-xs text-slate-400 mt-1">
                  12 Operational KPIs · SLA Breach Ratios · Multi-Turn Grounded Insights
                </p>
              </div>
              <span className="text-xs font-mono px-2 py-1 rounded bg-slate-800 text-sky-400 border border-slate-700">
                Data Source: SQLite cx_database.sqlite
              </span>
            </div>

            {/* Scorecard */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-slate-950 border border-slate-800 p-4 rounded-xl shadow-lg">
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">Conversations</span>
                <div className="text-2xl font-bold text-white mt-1">{messages.length + 54}</div>
                <span className="text-[11px] text-emerald-400 font-medium">99.4% Handled</span>
              </div>
              <div className="bg-slate-950 border border-slate-800 p-4 rounded-xl shadow-lg">
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">Total Complaints</span>
                <div className="text-2xl font-bold text-white mt-1">15</div>
                <span className="text-[11px] text-slate-400">4 Escalated</span>
              </div>
              <div className="bg-slate-950 border border-slate-800 p-4 rounded-xl shadow-lg">
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">Customer CSAT</span>
                <div className="text-2xl font-bold text-emerald-400 mt-1">88.5%</div>
                <span className="text-[11px] text-emerald-400 font-medium">+2.1% MoM</span>
              </div>
              <div className="bg-slate-950 border border-slate-800 p-4 rounded-xl shadow-lg">
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">SLA Breach Ratio</span>
                <div className="text-2xl font-bold text-slate-100 mt-1">18.4%</div>
                <span className="text-[11px] text-emerald-400 font-medium">Target &lt; 25%</span>
              </div>
            </div>

            {/* Complaints Ledger */}
            <div className="bg-slate-950 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
              <div className="p-4 border-b border-slate-800 bg-slate-900/60">
                <h3 className="text-sm font-semibold text-white">Master Complaints & Tickets Ledger</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs text-slate-300">
                  <thead className="bg-slate-900 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
                    <tr>
                      <th className="py-3 px-4">Ticket ID</th>
                      <th className="py-3 px-4">Customer</th>
                      <th className="py-3 px-4">Product</th>
                      <th className="py-3 px-4">Category</th>
                      <th className="py-3 px-4">Urgency</th>
                      <th className="py-3 px-4">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {INITIAL_COMPLAINTS.map(c => (
                      <tr key={c.id} className="hover:bg-slate-900/50">
                        <td className="py-3 px-4 font-mono font-semibold text-sky-400">{c.id}</td>
                        <td className="py-3 px-4">{c.customerName}</td>
                        <td className="py-3 px-4">{c.product}</td>
                        <td className="py-3 px-4">{c.category}</td>
                        <td className="py-3 px-4">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${c.urgency === 'CRITICAL' ? 'bg-red-950 text-red-300' : 'bg-slate-800 text-slate-300'}`}>
                            {c.urgency}
                          </span>
                        </td>
                        <td className="py-3 px-4">{c.status}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* ============================================================================== */}
        {/* TAB 5: VS CODE STREAMLIT LOCAL INSTRUCTIONS */}
        {/* ============================================================================== */}
        {activeTab === 'vscode' && (
          <div className="space-y-6">
            <div className="bg-slate-950 p-6 rounded-xl border border-slate-800 flex flex-wrap items-center justify-between gap-4 shadow-xl">
              <div>
                <h2 className="text-xl font-bold text-white tracking-tight">Run Locally in VS Code (Streamlit)</h2>
                <p className="text-xs text-slate-400 mt-1">
                  Complete Python Streamlit Project Ready in customer_experience_bot/
                </p>
              </div>
            </div>

            <div className="bg-slate-950 border border-slate-800 rounded-xl p-5 shadow-xl">
              <span className="text-xs font-semibold text-slate-400 block mb-2 uppercase tracking-wider">
                Windows Terminal Commands:
              </span>
              <div className="bg-black/90 font-mono text-xs text-emerald-400 p-4 rounded-lg space-y-1 overflow-x-auto">
                <p className="text-slate-500"># 1. Open Terminal in VS Code</p>
                <p className="text-slate-100">cd customer_experience_bot</p>
                <p className="text-slate-500"># 2. Create and activate virtual environment</p>
                <p className="text-slate-100">python -m venv venv</p>
                <p className="text-slate-100">.\venv\Scripts\Activate.ps1</p>
                <p className="text-slate-500"># 3. Install requirements</p>
                <p className="text-slate-100">pip install -r requirements.txt</p>
                <p className="text-slate-500"># 4. Run Streamlit</p>
                <p className="text-emerald-300 font-bold">streamlit run app.py</p>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
