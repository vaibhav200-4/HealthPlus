import { useState, useEffect, useRef, useCallback } from 'react';
import config from '../config';
import { useAuth } from '../context/AuthContext';

export type VoiceState = 'idle' | 'connecting' | 'listening' | 'speaking' | 'error';

export interface TranscriptItem {
  id: string;
  sender: 'user' | 'bot';
  text: string;
  timestamp: string;
}

export interface UseVoiceAgentOptions {
  onUserMessage?: (text: string) => void;
  onBotMessage?: (text: string, endCall?: boolean) => void;
}

export function useVoiceAgent(options?: UseVoiceAgentOptions) {
  const { token } = useAuth();
  const [state, setState] = useState<VoiceState>('idle');
  const [transcripts, setTranscripts] = useState<TranscriptItem[]>([]);
  const [isMuted, setIsMuted] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const onUserMessageRef = useRef(options?.onUserMessage);
  const onBotMessageRef = useRef(options?.onBotMessage);

  useEffect(() => {
    onUserMessageRef.current = options?.onUserMessage;
    onBotMessageRef.current = options?.onBotMessage;
  }, [options?.onUserMessage, options?.onBotMessage]);

  const isSpeechSupported = typeof window !== 'undefined' && !!(
    (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
  );

  const wsRef = useRef<WebSocket | null>(null);
  const recognitionRef = useRef<any>(null);
  const isBotSpeakingRef = useRef(false);
  const isMutedRef = useRef(false);
  const activeSessionIdRef = useRef<string | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 3;

  useEffect(() => {
    isMutedRef.current = isMuted;
    if (recognitionRef.current && state === 'listening') {
      if (isMuted) {
        try { recognitionRef.current.stop(); } catch (_) {}
      } else if (!isBotSpeakingRef.current) {
        try { recognitionRef.current.start(); } catch (_) {}
      }
    }
  }, [isMuted, state]);

  const unlockAudio = useCallback(() => {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      try {
        window.speechSynthesis.cancel();
        const silentUtterance = new SpeechSynthesisUtterance('');
        window.speechSynthesis.speak(silentUtterance);
      } catch (e) {
        console.warn('Audio unlock warning:', e);
      }
    }
  }, []);

  const speakText = useCallback((text: string, onFinish?: () => void) => {
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) {
      onFinish?.();
      return;
    }

    try {
      window.speechSynthesis.cancel();
      isBotSpeakingRef.current = true;
      setState('speaking');

      if (recognitionRef.current) {
        try { recognitionRef.current.stop(); } catch (_) {}
      }

      const cleanText = text.replace(/\[END_CALL\]/g, '').trim();
      if (!cleanText) {
        isBotSpeakingRef.current = false;
        if (!isMutedRef.current && recognitionRef.current) {
          try { recognitionRef.current.start(); } catch (_) {}
        }
        setState('listening');
        onFinish?.();
        return;
      }

      const utterance = new SpeechSynthesisUtterance(cleanText);
      utterance.lang = 'en-IN';
      utterance.rate = 1.0;

      const handleDone = () => {
        isBotSpeakingRef.current = false;
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          setState('listening');
          if (!isMutedRef.current && recognitionRef.current) {
            try { recognitionRef.current.start(); } catch (_) {}
          }
        }
        onFinish?.();
      };

      utterance.onend = handleDone;
      utterance.onerror = (e) => {
        console.warn('TTS error:', e);
        handleDone();
      };

      window.speechSynthesis.speak(utterance);
    } catch (err) {
      console.error('speechSynthesis exception:', err);
      isBotSpeakingRef.current = false;
      setState('listening');
      onFinish?.();
    }
  }, []);

  const sendText = useCallback((text: string) => {
    const trimmed = text.trim();
    if (!trimmed || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;

    const userItem: TranscriptItem = {
      id: Math.random().toString(),
      sender: 'user',
      text: trimmed,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
    setTranscripts((prev) => [...prev, userItem]);
    onUserMessageRef.current?.(trimmed);

    try {
      wsRef.current.send(JSON.stringify({ text: trimmed }));
    } catch (err) {
      console.error('Failed to send WS text:', err);
    }
  }, []);

  const stopRecognition = useCallback(() => {
    if (recognitionRef.current) {
      try {
        recognitionRef.current.onresult = null;
        recognitionRef.current.onerror = null;
        recognitionRef.current.onend = null;
        recognitionRef.current.stop();
      } catch (_) {}
      recognitionRef.current = null;
    }
  }, []);

  const startRecognition = useCallback(() => {
    if (!isSpeechSupported) return;
    stopRecognition();

    const SpeechRecognitionClass = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    const recognition = new SpeechRecognitionClass();
    recognition.continuous = true;
    recognition.interimResults = false;
    recognition.lang = 'en-IN';

    recognition.onresult = (event: any) => {
      if (isBotSpeakingRef.current || isMutedRef.current) return;

      for (let i = event.resultIndex; i < event.results.length; ++i) {
        const res = event.results[i];
        if (res.isFinal) {
          const spokenText = res[0]?.transcript?.trim();
          if (spokenText) {
            sendText(spokenText);
          }
        }
      }
    };

    recognition.onerror = (event: any) => {
      if (event.error === 'not-allowed' || event.error === 'service-not-allowed') {
        setErrorMessage('Microphone access denied. Please enable mic permissions in your browser settings.');
        setState('error');
      } else if (event.error !== 'no-speech' && event.error !== 'aborted') {
        console.warn('Speech recognition warning:', event.error);
      }
    };

    recognition.onend = () => {
      if (!isBotSpeakingRef.current && !isMutedRef.current && wsRef.current?.readyState === WebSocket.OPEN) {
        try { recognition.start(); } catch (_) {}
      }
    };

    recognitionRef.current = recognition;
    try {
      recognition.start();
    } catch (e) {
      console.warn('Recognition start error:', e);
    }
  }, [isSpeechSupported, sendText, stopRecognition]);

  const disconnectSession = useCallback(() => {
    stopRecognition();
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      try { window.speechSynthesis.cancel(); } catch (_) {}
    }
    isBotSpeakingRef.current = false;
    if (wsRef.current) {
      wsRef.current.onclose = null;
      wsRef.current.onerror = null;
      wsRef.current.onmessage = null;
      try { wsRef.current.close(); } catch (_) {}
      wsRef.current = null;
    }
    setState('idle');
    activeSessionIdRef.current = null;
  }, [stopRecognition]);

  const buildWsUrl = useCallback((wsPath: string) => {
    let baseUrl: string;
    const envWsUrl = import.meta.env.VITE_WS_URL;
    if (envWsUrl && typeof envWsUrl === 'string' && envWsUrl.trim() !== '') {
      baseUrl = envWsUrl.trim().replace(/\/+$/, '');
      return `${baseUrl}${wsPath}`;
    }

    const apiUrl = new URL(config.apiBaseUrl);
    const protocol = apiUrl.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${protocol}//${apiUrl.host}${wsPath}`;
  }, []);

  const connectSession = useCallback(async () => {
    unlockAudio();
    disconnectSession();
    setErrorMessage(null);
    setTranscripts([]);
    setState('connecting');
    reconnectAttemptsRef.current = 0;

    try {
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const sessionRes = await fetch(`${config.apiBaseUrl}/voice/session`, {
        method: 'POST',
        headers,
      });

      if (!sessionRes.ok) {
        throw new Error(`Failed to create voice session: ${sessionRes.statusText}`);
      }

      const sessionData = await sessionRes.json();
      const wsPath = sessionData.ws_url; // e.g. /api/voice/ws/{session_id}
      let wsUrl = buildWsUrl(wsPath);

      if (token) {
        wsUrl += `${wsUrl.includes('?') ? '&' : '?'}token=${encodeURIComponent(token)}`;
      }

      activeSessionIdRef.current = sessionData.session_id;

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setState('listening');
        if (isSpeechSupported && !isMutedRef.current) {
          startRecognition();
        }
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'bot_text') {
            const botMsg = data.text || '';
            const botItem: TranscriptItem = {
              id: Math.random().toString(),
              sender: 'bot',
              text: botMsg,
              timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            };
            setTranscripts((prev) => [...prev, botItem]);
            onBotMessageRef.current?.(botMsg, Boolean(data.end_call));

            speakText(botMsg, () => {
              if (data.end_call) {
                disconnectSession();
              }
            });
          } else if (data.type === 'error') {
            setErrorMessage(data.message || 'Voice agent error occurred.');
            setState('error');
          }
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e);
        }
      };

      ws.onerror = (event) => {
        console.error('Voice WebSocket error:', event);
        setErrorMessage('Voice connection error.');
        setState('error');
      };

      ws.onclose = () => {
        if (activeSessionIdRef.current && reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current += 1;
          const delay = Math.pow(2, reconnectAttemptsRef.current) * 500;
          setTimeout(() => {
            if (activeSessionIdRef.current) {
              connectSession();
            }
          }, delay);
        } else {
          disconnectSession();
        }
      };
    } catch (err: any) {
      console.error('Voice agent connection failure:', err);
      setErrorMessage(err.message || 'Failed to start voice session.');
      setState('error');
    }
  }, [token, unlockAudio, disconnectSession, buildWsUrl, isSpeechSupported, startRecognition, speakText]);

  const toggleMute = useCallback(() => {
    setIsMuted((prev) => !prev);
  }, []);

  useEffect(() => {
    return () => {
      disconnectSession();
    };
  }, [disconnectSession]);

  return {
    state,
    transcripts,
    isMuted,
    errorMessage,
    isSpeechSupported,
    connectSession,
    disconnectSession,
    sendText,
    toggleMute,
  };
}
