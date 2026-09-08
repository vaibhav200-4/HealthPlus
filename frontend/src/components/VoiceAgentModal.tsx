import React, { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, Phone, PhoneOff, X, Volume2, Sparkles, AlertCircle, RefreshCw } from 'lucide-react';

interface VoiceAgentModalProps {
  isOpen: boolean;
  onClose: () => void;
}

interface MessageItem {
  id: string;
  sender: 'user' | 'bot';
  text: string;
  timestamp: string;
}

export const VoiceAgentModal: React.FC<VoiceAgentModalProps> = ({ isOpen, onClose }) => {
  const [isCalling, setIsCalling] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [messages, setMessages] = useState<MessageItem[]>([]);
  const [transcript, setTranscript] = useState('');
  const [statusText, setStatusText] = useState('Ready to connect');
  const [telephonyNumber, setTelephonyNumber] = useState('+91-1800-HEALTHPLUS');
  const [activeVisualizer, setActiveVisualizer] = useState(false);

  const socketRef = useRef<WebSocket | null>(null);
  const recognitionRef = useRef<any>(null);
  const isCallingRef = useRef(false);
  const isMutedRef = useRef(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Fetch Telephony Info on mount
  useEffect(() => {
    fetch('/api/voice/telephony-info')
      .then((res) => res.json())
      .then((data) => {
        if (data.phone_number) {
          setTelephonyNumber(data.phone_number);
        }
      })
      .catch(() => {
        // Default fallback number
      });
  }, []);

  // Auto scroll transcript
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, statusText]);

  // ── Guard flag: true while the bot is speaking via SpeechSynthesis ─────────
  const botSpeakingRef = useRef(false);
  // Last text the bot spoke – used for post-speech overlap filter
  const lastBotTextRef = useRef('');

  // ── Token-overlap echo detector (mirrors server-side logic) ──────────────
  const echoOverlapRatio = (userText: string, botText: string): number => {
    if (!userText || !botText) return 0;
    const clean = (s: string) => s.toLowerCase().replace(/[^a-z0-9 ]/g, '').split(/\s+/).filter(Boolean);
    const ua = new Set(clean(userText));
    const ba = new Set(clean(botText));
    if (ua.size === 0) return 0;
    let shared = 0;
    ua.forEach(w => { if (ba.has(w)) shared++; });
    return shared / ua.size;
  };

  // Get best available Indian Female voice from browser SpeechSynthesis
  const getIndianFemaleVoice = (): SpeechSynthesisVoice | null => {
    if (!('speechSynthesis' in window)) return null;
    const voices = window.speechSynthesis.getVoices();
    if (!voices || voices.length === 0) return null;

    // 1. Look for explicit Indian Female voices
    const inFemale = voices.find(v => 
      (v.lang.includes('en-IN') || v.lang.includes('hi-IN') || v.lang.includes('ta-IN') || v.lang.includes('te-IN')) &&
      (v.name.toLowerCase().includes('female') || v.name.toLowerCase().includes('google') || v.name.toLowerCase().includes('neerja') || v.name.toLowerCase().includes('heera') || v.name.toLowerCase().includes('veena') || v.name.toLowerCase().includes('komal') || v.name.toLowerCase().includes('maya') || v.name.toLowerCase().includes('zira'))
    );
    if (inFemale) return inFemale;

    // 2. Look for any Indian voice (en-IN or hi-IN)
    const inVoice = voices.find(v => v.lang.includes('en-IN') || v.lang.includes('hi-IN'));
    if (inVoice) return inVoice;

    // 3. Look for any female voice (English)
    const femaleVoice = voices.find(v => v.lang.startsWith('en') && (v.name.toLowerCase().includes('female') || v.name.toLowerCase().includes('zira') || v.name.toLowerCase().includes('samantha') || v.name.toLowerCase().includes('victoria') || v.name.toLowerCase().includes('karen')));
    if (femaleVoice) return femaleVoice;

    return null;
  };

  // Setup Speech Recognition
  const initSpeechRecognition = (socket: WebSocket) => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setStatusText('Browser speech recognition not natively supported. Type to send.');
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'en-IN';

      recognition.onresult = (event: any) => {
        // ── HARD BLOCK: drop everything while bot is speaking ────────────
        if (botSpeakingRef.current) return;

        let interim = '';
        let final = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const trans = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            final += trans;
          } else {
            interim += trans;
          }
        }

        if (interim) {
          setTranscript(interim);
        }

        if (final.trim() && socket && socket.readyState === WebSocket.OPEN) {
          const trimmed = final.trim();

          // ── Token-overlap echo filter ────────────────────────────────────
          // Reject if >55% of words match what the bot just said
          if (lastBotTextRef.current && trimmed.split(/\s+/).length > 2) {
            const overlap = echoOverlapRatio(trimmed, lastBotTextRef.current);
            if (overlap >= 0.55) {
              console.warn(`[ECHO FILTER] Dropped (overlap=${overlap.toFixed(2)}): "${trimmed}"`);
              setTranscript('');
              return;
            }
          }

          const userMsg: MessageItem = {
            id: Date.now().toString(),
            sender: 'user',
            text: trimmed,
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
          };
          setMessages((prev) => [...prev, userMsg]);
          setTranscript('');

          socket.send(JSON.stringify({ text: trimmed }));
          setStatusText('AI Assistant is processing...');
          setActiveVisualizer(true);
        }
      };

      recognition.onerror = (err: any) => {
        console.warn('Speech recognition error:', err);
      };

      recognition.onend = () => {
        // Only restart if: call active AND not muted AND bot is NOT speaking
        if (isCallingRef.current && !isMutedRef.current && !botSpeakingRef.current && recognitionRef.current === recognition) {
          window.setTimeout(() => {
            try { recognition.start(); } catch (e) {}
          }, 100);
        }
      };

      recognitionRef.current = recognition;
      recognition.start();
    } catch (e) {
      console.error('Failed to start speech recognition:', e);
    }
  };

  // Speak AI responses using Web Speech Synthesis
  const speakText = (text: string) => {
    if (!('speechSynthesis' in window)) return;
    try {
      // ── Step 1: Mark bot as speaking & record what it will say ──────────
      botSpeakingRef.current = true;
      lastBotTextRef.current = text;

      // ── Step 2: Stop recognition BEFORE TTS starts speaking ─────────────
      if (recognitionRef.current) {
        try { recognitionRef.current.stop(); } catch (e) {}
      }

      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      
      const chosenVoice = getIndianFemaleVoice();
      if (chosenVoice) {
        utterance.voice = chosenVoice;
      }
      utterance.rate = 1.18;
      utterance.pitch = 1.15;
      utterance.lang = 'en-IN';

      utterance.onstart = () => {
        // Double-ensure recognition is stopped once speech actually starts
        if (recognitionRef.current) {
          try { recognitionRef.current.stop(); } catch (e) {}
        }
        setActiveVisualizer(true);
        setStatusText('Aradhya Mishra is speaking...');
      };

      utterance.onend = () => {
        setActiveVisualizer(false);
        setStatusText('Listening for your response...');

        // ── Step 3: 200ms cooldown after TTS ends before re-enabling mic ──
        window.setTimeout(() => {
          botSpeakingRef.current = false;
          if (isCallingRef.current && !isMutedRef.current && recognitionRef.current) {
            try { recognitionRef.current.start(); } catch (e) {}
          }
        }, 200);
      };

      utterance.onerror = () => {
        // Make sure we re-enable mic even on TTS error
        botSpeakingRef.current = false;
        if (isCallingRef.current && !isMutedRef.current && recognitionRef.current) {
          try { recognitionRef.current.start(); } catch (e) {}
        }
      };

      window.speechSynthesis.speak(utterance);
    } catch (e) {
      botSpeakingRef.current = false;
      console.warn('Speech Synthesis error:', e);
    }
  };


  const startVoiceCall = async () => {
    try {
      setStatusText('Connecting to AI Voice Agent...');
      const res = await fetch('/api/voice/session', { method: 'POST' });
      const data = await res.json();

      const path = data.ws_url || `/api/voice/ws/${data.session_id}`;
      let wsUrl = '';
      const apiUrl = import.meta.env.VITE_API_URL;
      
      if (apiUrl && !apiUrl.includes('localhost:5173')) {
        try {
          const urlObj = new URL(apiUrl);
          const wsProtocol = urlObj.protocol === 'https:' ? 'wss:' : 'ws:';
          wsUrl = `${wsProtocol}//${urlObj.host}${path}`;
        } catch (e) {
          const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
          wsUrl = `${protocol}//${window.location.host}${path}`;
        }
      } else {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        wsUrl = `${protocol}//${window.location.host}${path}`;
      }

      const socket = new WebSocket(wsUrl);
      socketRef.current = socket;

      socket.onopen = () => {
        setIsCalling(true);
        isCallingRef.current = true;
        setStatusText('Connected! Speak into your microphone...');
        initSpeechRecognition(socket);
      };

      socket.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === 'bot_text') {
            const botMsg: MessageItem = {
              id: Date.now().toString(),
              sender: 'bot',
              text: msg.text,
              timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            };
            setMessages((prev) => [...prev, botMsg]);
            speakText(msg.text);

            if (msg.end_call) {
              setTimeout(() => endVoiceCall(), 3000);
            }
          }
        } catch (e) {
          console.error('WebSocket parse error:', e);
        }
      };

      socket.onerror = (err) => {
        console.error('WebSocket connection error:', err);
        setStatusText('Connection error. Retrying...');
      };

      socket.onclose = () => {
        isCallingRef.current = false;
        setIsCalling(false);
        setStatusText('Call ended.');
        if (recognitionRef.current) {
          try { recognitionRef.current.stop(); } catch(e) {}
        }
      };
    } catch (e) {
      console.error('Failed to initiate voice call:', e);
      setStatusText('Failed to connect to Voice Agent.');
    }
  };

  const endVoiceCall = () => {
    isCallingRef.current = false;
    if (socketRef.current) {
      socketRef.current.close();
      socketRef.current = null;
    }
    if (recognitionRef.current) {
      try { recognitionRef.current.stop(); } catch(e) {}
      recognitionRef.current = null;
    }
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    setIsCalling(false);
    setActiveVisualizer(false);
    setStatusText('Call ended.');
  };

  const toggleMute = () => {
    const nextMuted = !isMutedRef.current;
    isMutedRef.current = nextMuted;
    setIsMuted(nextMuted);
    if (nextMuted) {
      // Stop recognition AND stop any ongoing TTS when muting
      if (recognitionRef.current) {
        try { recognitionRef.current.stop(); } catch(e) {}
      }
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
      botSpeakingRef.current = false;
    } else if (!nextMuted && socketRef.current && !botSpeakingRef.current) {
      // Only restart recognition if bot is not currently speaking
      try { recognitionRef.current?.start(); } catch(e) {}
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="relative w-full max-w-lg bg-gradient-to-b from-slate-900 via-slate-800 to-slate-950 text-white rounded-3xl shadow-2xl border border-slate-700/60 overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="p-5 bg-slate-800/80 border-b border-slate-700 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="w-11 h-11 rounded-2xl bg-gradient-to-tr from-emerald-500 to-teal-400 flex items-center justify-center shadow-lg shadow-emerald-500/20">
                <Sparkles className="w-6 h-6 text-slate-950" />
              </div>
              {isCalling && (
                <span className="absolute -top-1 -right-1 w-3.5 h-3.5 bg-emerald-400 rounded-full border-2 border-slate-900 animate-ping" />
              )}
            </div>
            <div>
              <h3 className="font-bold text-base text-white">Aradhya Mishra</h3>
              <p className="text-xs text-slate-400">HealthPlus AI Voice Assistant</p>
            </div>
          </div>

          <button
            onClick={() => {
              endVoiceCall();
              onClose();
            }}
            className="p-2 text-slate-400 hover:text-white rounded-full hover:bg-slate-700/50 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Telephony Banner */}
        <div className="px-5 py-2.5 bg-emerald-950/40 border-b border-emerald-800/40 flex items-center justify-between text-xs text-emerald-300">
          <div className="flex items-center gap-2">
            <Phone className="w-4 h-4 text-emerald-400" />
            <span>Telephony Hotline: <strong className="text-white">{telephonyNumber}</strong></span>
          </div>
          <a
            href={`tel:${telephonyNumber}`}
            className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold rounded-lg transition-colors shadow-sm"
          >
            Dial Phone
          </a>
        </div>

        {/* Voice Visualizer Area */}
        <div className="p-6 flex flex-col items-center justify-center border-b border-slate-800 bg-slate-900/40">
          <div className="relative flex items-center justify-center my-4">
            {/* Wave Rings */}
            {isCalling && activeVisualizer && (
              <>
                <div className="absolute w-36 h-36 rounded-full bg-emerald-500/20 animate-ping opacity-75" />
                <div className="absolute w-48 h-48 rounded-full bg-teal-500/10 animate-pulse" />
              </>
            )}

            <button
              onClick={isCalling ? endVoiceCall : startVoiceCall}
              className={`relative z-10 w-24 h-24 rounded-full flex items-center justify-center shadow-2xl transition-all duration-300 transform hover:scale-105 ${
                isCalling
                  ? 'bg-gradient-to-br from-red-500 to-rose-600 shadow-red-500/30'
                  : 'bg-gradient-to-br from-emerald-500 to-teal-600 shadow-emerald-500/30'
              }`}
            >
              {isCalling ? <PhoneOff className="w-10 h-10 text-white" /> : <Mic className="w-10 h-10 text-white" />}
            </button>
          </div>

          <p className="mt-2 text-xs font-medium text-emerald-400 animate-pulse text-center">
            {statusText}
          </p>

          {transcript && (
            <div className="mt-3 px-4 py-2 bg-slate-800/80 border border-slate-700 rounded-xl text-xs text-slate-300 max-w-xs text-center">
              "{transcript}"
            </div>
          )}
        </div>

        {/* Conversation Transcript */}
        <div className="flex-1 p-4 overflow-y-auto space-y-3 min-h-[160px] max-h-[260px] bg-slate-950/60 text-xs">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-slate-500 text-center py-6">
              <Volume2 className="w-8 h-8 text-slate-600 mb-2" />
              <p>Press the green mic button to start your voice call</p>
              <p className="text-[11px] text-slate-600 mt-1">Or dial <strong className="text-slate-400">{telephonyNumber}</strong> directly from your phone</p>
            </div>
          ) : (
            messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex flex-col ${msg.sender === 'user' ? 'items-end' : 'items-start'}`}
              >
                <div
                  className={`max-w-[85%] px-3.5 py-2.5 rounded-2xl ${
                    msg.sender === 'user'
                      ? 'bg-emerald-600 text-white rounded-br-none'
                      : 'bg-slate-800 border border-slate-700 text-slate-200 rounded-bl-none'
                  }`}
                >
                  <p>{msg.text}</p>
                </div>
                <span className="text-[10px] text-slate-500 mt-1 px-1">{msg.timestamp}</span>
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Action Controls */}
        <div className="p-4 bg-slate-900 border-t border-slate-800 flex items-center justify-around">
          <button
            onClick={toggleMute}
            disabled={!isCalling}
            className={`p-3 rounded-2xl border transition-all ${
              isMuted
                ? 'bg-rose-500/20 border-rose-500/40 text-rose-400'
                : 'bg-slate-800 border-slate-700 text-slate-300 hover:text-white'
            } disabled:opacity-40 disabled:cursor-not-allowed`}
          >
            {isMuted ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
          </button>

          <button
            onClick={isCalling ? endVoiceCall : startVoiceCall}
            className={`px-6 py-3 rounded-2xl font-semibold text-sm flex items-center gap-2 transition-all shadow-md ${
              isCalling
                ? 'bg-rose-600 hover:bg-rose-700 text-white shadow-rose-600/20'
                : 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-emerald-600/20'
            }`}
          >
            {isCalling ? (
              <>
                <PhoneOff className="w-4 h-4" /> End Call
              </>
            ) : (
              <>
                <Mic className="w-4 h-4" /> Start Voice Call
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
