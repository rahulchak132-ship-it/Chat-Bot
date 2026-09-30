import http from 'http';
import path from 'path';
import { fileURLToPath } from 'url';
import express, { Request, Response } from 'express';
import dotenv from 'dotenv';
import { WebSocketServer, WebSocket } from 'ws';
import { GoogleGenAI, LiveServerMessage, Modality } from '@google/genai';

dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const server = http.createServer(app);
const port = process.env.PORT ? parseInt(process.env.PORT) : 3000;

// Increase payload limits for base64 audio transcription
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ extended: true, limit: '50mb' }));

// Shared Gemini client configured with telemetry header
const ai = new GoogleGenAI({
  apiKey: process.env.GEMINI_API_KEY,
  httpOptions: {
    headers: {
      'User-Agent': 'aistudio-build',
    },
  },
});

// ============================================================================
// 1. GEMINI MULTI-TURN CHAT ENDPOINT
// Models: gemini-3.1-pro-preview (complex), gemini-3.5-flash (general), gemini-3.1-flash-lite (fast)
// ============================================================================
app.post('/api/gemini/chat', async (req: Request, res: Response) => {
  try {
    const { messages, systemInstruction, model = 'gemini-3.5-flash', roleConfig } = req.body;

    if (!messages || !Array.isArray(messages)) {
      return res.status(400).json({ error: 'Messages array is required.' });
    }

    // Determine model alias
    let selectedModel = model;
    if (model === 'complex' || model === 'gemini-pro') {
      selectedModel = 'gemini-3.1-pro-preview';
    } else if (model === 'fast' || model === 'gemini-lite') {
      selectedModel = 'gemini-3.1-flash-lite';
    } else if (model === 'general' || model === 'gemini-flash') {
      selectedModel = 'gemini-3.5-flash';
    }

    // Format contents for multi-turn chat
    const contents = messages.map((m: { role: string; content: string }) => ({
      role: m.role === 'assistant' || m.role === 'model' ? 'model' : 'user',
      parts: [{ text: m.content || '' }],
    }));

    const defaultSystemInstruction =
      systemInstruction ||
      `You are the Senior Customer Experience & Service Executive for Apex Global Technologies & Systems.
You assist retail customers, authorized dealers, and regional distributors with solar inverters, commercial heat pumps, EV fast chargers, and industrial pumps.
- Be polite, empathetic, concise, and solution-oriented.
- When an angry customer reaches out, acknowledge their frustration first.
- If verified technical details or warranty specifications are not known, politely state that you can raise a service request rather than guessing.
- Help troubleshoot errors (e.g. Error E04 relay issue, E01 overvoltage, thermal cut-offs).`;

    const response = await ai.models.generateContent({
      model: selectedModel,
      contents,
      config: {
        systemInstruction: defaultSystemInstruction,
        temperature: 0.3,
      },
    });

    const replyText = response.text || 'I have received your inquiry and noted the details.';
    res.json({
      text: replyText,
      role: 'model',
      modelUsed: selectedModel,
    });
  } catch (error: any) {
    console.error('Error in /api/gemini/chat:', error);
    res.status(500).json({
      error: error.message || 'Failed to generate response from Gemini.',
    });
  }
});

// ============================================================================
// 2. AUDIO TRANSCRIPTION ENDPOINT
// Model: gemini-3.5-transcribe
// ============================================================================
app.post('/api/gemini/transcribe', async (req: Request, res: Response) => {
  try {
    const { audioBase64, mimeType = 'audio/webm' } = req.body;

    if (!audioBase64) {
      return res.status(400).json({ error: 'audioBase64 string is required.' });
    }

    // Clean data URL prefix if present
    const cleanBase64 = audioBase64.replace(/^data:[^;]+;base64,/, '');

    const response = await ai.models.generateContent({
      model: 'gemini-3.5-transcribe',
      contents: {
        parts: [
          {
            inlineData: {
              mimeType,
              data: cleanBase64,
            },
          },
          {
            text: 'Transcribe this customer or technician audio recording verbatim. Provide a clean, accurate transcription of all spoken dialogue.',
          },
        ],
      },
    });

    const transcription = response.text || '';
    res.json({
      transcription,
      modelUsed: 'gemini-3.5-transcribe',
    });
  } catch (error: any) {
    console.error('Error in /api/gemini/transcribe:', error);
    res.status(500).json({
      error: error.message || 'Failed to transcribe audio with gemini-3.5-transcribe.',
    });
  }
});

// ============================================================================
// 3. WEBSOCKET SERVER FOR VOICE CONVERSATIONS (LIVE API)
// Model: gemini-3.8-live
// ============================================================================
const wss = new WebSocketServer({ noServer: true });

wss.on('connection', async (clientWs: WebSocket) => {
  console.log('[Live API] Client connected for real-time voice conversation');
  let session: any = null;

  try {
    session = await ai.live.connect({
      model: 'gemini-3.8-live',
      config: {
        responseModalities: [Modality.AUDIO],
        speechConfig: {
          voiceConfig: { prebuiltVoiceConfig: { voiceName: 'Zephyr' } },
        },
        systemInstruction: `You are the Apex Global AI Voice Customer Experience Executive speaking to a customer, dealer, or distributor over phone/voice.
Keep spoken responses short, natural, empathetic, and conversational (1 to 3 sentences).
Always acknowledge frustration first if the caller is unhappy with a delay or equipment fault.`,
      },
      callbacks: {
        onmessage: (message: LiveServerMessage) => {
          // Model audio response chunk (PCM 24kHz)
          const audio = message.serverContent?.modelTurn?.parts?.[0]?.inlineData?.data;
          const text = message.serverContent?.modelTurn?.parts?.[0]?.text;

          if (audio && clientWs.readyState === WebSocket.OPEN) {
            clientWs.send(JSON.stringify({ type: 'audio', audio }));
          }

          if (text && clientWs.readyState === WebSocket.OPEN) {
            clientWs.send(JSON.stringify({ type: 'text', text }));
          }

          if (message.serverContent?.interrupted && clientWs.readyState === WebSocket.OPEN) {
            clientWs.send(JSON.stringify({ type: 'interrupted', interrupted: true }));
          }

          if (message.serverContent?.turnComplete && clientWs.readyState === WebSocket.OPEN) {
            clientWs.send(JSON.stringify({ type: 'turnComplete' }));
          }
        },
        onclose: () => {
          if (clientWs.readyState === WebSocket.OPEN) {
            clientWs.send(JSON.stringify({ type: 'sessionClosed' }));
          }
        },
        onerror: (err: any) => {
          console.error('[Live API Session Error]:', err);
          if (clientWs.readyState === WebSocket.OPEN) {
            clientWs.send(JSON.stringify({ type: 'error', error: err.message || 'Live session error' }));
          }
        },
      },
    });

    clientWs.send(JSON.stringify({ type: 'ready', model: 'gemini-3.8-live' }));
  } catch (err: any) {
    console.error('[Live API Connection Failed]:', err);
    clientWs.send(JSON.stringify({ type: 'error', error: err.message || 'Failed to connect to Live API.' }));
  }

  clientWs.on('message', (rawData) => {
    try {
      const msg = JSON.parse(rawData.toString());
      if (session) {
        if (msg.audio) {
          // Real-time microphone audio chunk (base64 PCM 16kHz)
          session.sendRealtimeInput({
            audio: {
              data: msg.audio,
              mimeType: 'audio/pcm;rate=16000',
            },
          });
        } else if (msg.text) {
          // Real-time user text interruption/prompt
          session.sendRealtimeInput({
            text: msg.text,
          });
        }
      }
    } catch (parseErr) {
      console.error('Error handling WebSocket message:', parseErr);
    }
  });

  clientWs.on('close', () => {
    console.log('[Live API] Client disconnected');
    if (session && typeof session.close === 'function') {
      try {
        session.close();
      } catch (e) {
        // ignore
      }
    }
  });
});

// Route HTTP Upgrade to WebSocket server
server.on('upgrade', (request, socket, head) => {
  const { pathname } = new URL(request.url || '', `http://${request.headers.host}`);
  if (pathname === '/api/live' || pathname === '/live') {
    wss.handleUpgrade(request, socket, head, (ws) => {
      wss.emit('connection', ws, request);
    });
  }
});

// ============================================================================
// MOUNT VITE IN DEV OR SERVE STATIC IN PROD
// ============================================================================
async function startServer() {
  if (process.env.NODE_ENV !== 'production') {
    const { createServer: createViteServer } = await import('vite');
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: 'spa',
    });
    app.use(vite.middlewares);
  } else {
    app.use(express.static(path.resolve(__dirname, 'dist')));
    app.get('*', (_req: Request, res: Response) => {
      res.sendFile(path.resolve(__dirname, 'dist', 'index.html'));
    });
  }

  server.listen(port, '0.0.0.0', () => {
    console.log(`[Apex CX Server] Running on http://0.0.0.0:${port}`);
    console.log(`[Gemini Endpoints Ready]: /api/gemini/chat, /api/gemini/transcribe, /api/live`);
  });
}

startServer();
