import React, { useState, useRef, useEffect } from "react";
import { Send, Sparkles, RefreshCw, BookOpen, Layers, CheckCircle, BarChart2 } from "lucide-react";

interface StructuredPayload {
  summary: string;
  overall_confidence: number;
  prediction_confidence: number;
  knowledge_confidence: number;
  decision_confidence: number;
  rag_score: number;
  root_cause: string;
  business_impact: string;
  blast_radius: string;
  recommended_actions: string[];
  references: string[];
}

interface Message {
  sender: "user" | "copilot";
  text: string;
  timestamp: string;
  statusText?: string;
  isStreaming?: boolean;
  structuredResponse?: StructuredPayload;
}

interface CopilotChatProps {
  playbookLogs: string[];
}

export const CopilotChat: React.FC<CopilotChatProps> = ({
  playbookLogs,
}) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      sender: "copilot",
      text: "Hello! I am **Nexus AI Copilot**, operational in air-gapped NOC mode. I continuously analyze the SD-WAN digital twin, predict anomalies, and fetch local runbooks. Ask me any troubleshooting queries, or click a prompt below.",
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);
  const [inputValue, setInputValue] = useState("");
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [wsConnected, setWsConnected] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  // Initialize Copilot WebSocket connection
  useEffect(() => {
    const connectWs = () => {
      const ws = new WebSocket("ws://localhost:8000/ws/copilot?session_id=noc_operator_session");
      wsRef.current = ws;

      ws.onopen = () => {
        setWsConnected(true);
        console.log("Copilot WebSocket connected.");
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === "status") {
          setStatusMessage(data.message);
        } else if (data.type === "chunk") {
          setStatusMessage(null);
          setMessages((prev) => {
            const next = [...prev];
            const last = next[next.length - 1];
            if (last && last.sender === "copilot" && last.isStreaming) {
              last.text += data.chunk;
            } else {
              next.push({
                sender: "copilot",
                text: data.chunk,
                timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                isStreaming: true
              });
            }
            return next;
          });
        } else if (data.type === "final") {
          setStatusMessage(null);
          const payload = data.payload as StructuredPayload;
          setMessages((prev) => {
            const next = [...prev];
            // Remove the temporary streaming message if it exists
            const last = next[next.length - 1];
            if (last && last.sender === "copilot" && last.isStreaming) {
              next.pop();
            }
            next.push({
              sender: "copilot",
              text: payload.summary,
              timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
              structuredResponse: payload
            });
            return next;
          });
        }
      };

      ws.onclose = () => {
        setWsConnected(false);
        console.warn("Copilot WebSocket disconnected. Reconnecting in 3s...");
        setTimeout(connectWs, 3000);
      };
    };

    connectWs();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, playbookLogs, statusMessage]);

  const handleSend = () => {
    if (!inputValue.trim()) return;

    const userMsgText = inputValue;
    setInputValue("");

    // Add user message to UI
    setMessages((prev) => [
      ...prev,
      {
        sender: "user",
        text: userMsgText,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      }
    ]);

    // Send query over WebSocket if connected, otherwise fallback HTTP POST
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ message: userMsgText }));
    } else {
      // Fallback API request if WebSocket disconnected
      setStatusMessage("Connecting to offline RAG engine...");
      fetch("http://localhost:8000/api/copilot/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMsgText, session_id: "noc_operator_session" })
      })
        .then((res) => res.json())
        .then((data: StructuredPayload) => {
          setStatusMessage(null);
          setMessages((prev) => [
            ...prev,
            {
              sender: "copilot",
              text: data.summary,
              timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
              structuredResponse: data
            }
          ]);
        })
        .catch((err) => {
          setStatusMessage(null);
          console.error(err);
        });
    }
  };

  const triggerPrompt = (promptText: string) => {
    setInputValue(promptText);
    setTimeout(handleSend, 50);
  };

  return (
    <div className="glass-panel rounded-xl flex flex-col h-[560px] border border-white/5 shadow-2xl relative overflow-hidden">
      {/* Header */}
      <div className="px-5 py-3 border-b border-white/5 flex justify-between items-center bg-slate-900/40 backdrop-blur-sm z-10">
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-indigo-400 animate-pulse-slow" />
          <h2 className="font-bold text-slate-200 text-xs sm:text-sm">Autonomous NOC Copilot</h2>
        </div>
        <span className={`text-[9px] px-2 py-0.5 rounded-full font-mono border ${
          wsConnected 
            ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" 
            : "bg-amber-500/10 text-amber-400 border-amber-500/20"
        }`}>
          {wsConnected ? "STREAMING ACTIVE" : "REST MODE"}
        </span>
      </div>

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs sm:text-sm scrollbar-thin">
        {messages.map((msg, index) => (
          <div
            key={index}
            className={`flex flex-col ${msg.sender === "user" ? "items-end" : "items-start"}`}
          >
            <div
              className={`max-w-[90%] rounded-xl p-3.5 border ${
                msg.sender === "user"
                  ? "bg-indigo-600/30 border-indigo-500/30 text-slate-200 rounded-br-none"
                  : "bg-slate-900/60 border-white/5 text-slate-300 rounded-bl-none"
              }`}
            >
              {/* Raw Text Output */}
              <div className="space-y-1.5 leading-relaxed break-words whitespace-pre-line text-xs font-sans">
                {msg.text}
              </div>

              {/* Structured JSON Rendering Compartments */}
              {msg.structuredResponse && (
                <div className="mt-4 pt-3 border-t border-white/5 space-y-3.5 text-[11px] font-sans">
                  
                  {/* Confidence breakdown */}
                  <div className="bg-slate-950/60 p-2.5 rounded-lg border border-white/5 space-y-2">
                    <div className="flex justify-between items-center text-[10px] text-muted-foreground font-bold">
                      <span className="flex items-center gap-1"><BarChart2 className="w-3.5 h-3.5 text-indigo-400" /> Overall Confidence</span>
                      <span className="text-indigo-400 font-mono">{(msg.structuredResponse.overall_confidence * 100).toFixed(0)}%</span>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-2 text-[9px] font-mono text-slate-300">
                      <div>
                        <div className="flex justify-between">
                          <span className="text-slate-500">Predictive:</span>
                          <span>{(msg.structuredResponse.prediction_confidence * 100).toFixed(0)}%</span>
                        </div>
                        <div className="w-full bg-slate-900 h-1.5 rounded-full overflow-hidden mt-0.5">
                          <div className="bg-indigo-500 h-full" style={{ width: `${msg.structuredResponse.prediction_confidence * 100}%` }} />
                        </div>
                      </div>
                      <div>
                        <div className="flex justify-between">
                          <span className="text-slate-500">KB Match:</span>
                          <span>{(msg.structuredResponse.knowledge_confidence * 100).toFixed(0)}%</span>
                        </div>
                        <div className="w-full bg-slate-900 h-1.5 rounded-full overflow-hidden mt-0.5">
                          <div className="bg-cyan-500 h-full" style={{ width: `${msg.structuredResponse.knowledge_confidence * 100}%` }} />
                        </div>
                      </div>
                      <div>
                        <div className="flex justify-between">
                          <span className="text-slate-500">Decision:</span>
                          <span>{(msg.structuredResponse.decision_confidence * 100).toFixed(0)}%</span>
                        </div>
                        <div className="w-full bg-slate-900 h-1.5 rounded-full overflow-hidden mt-0.5">
                          <div className="bg-emerald-500 h-full" style={{ width: `${msg.structuredResponse.decision_confidence * 100}%` }} />
                        </div>
                      </div>
                      <div>
                        <div className="flex justify-between">
                          <span className="text-slate-500">RAG Score:</span>
                          <span>{(msg.structuredResponse.rag_score * 100).toFixed(0)}%</span>
                        </div>
                        <div className="w-full bg-slate-900 h-1.5 rounded-full overflow-hidden mt-0.5">
                          <div className="bg-rose-500 h-full" style={{ width: `${msg.structuredResponse.rag_score * 100}%` }} />
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Multi-Agent steps details */}
                  <div className="space-y-1 bg-slate-950/40 p-2.5 border border-white/5 rounded-lg">
                    <span className="text-[10px] text-muted-foreground uppercase font-bold tracking-wider flex items-center gap-1">
                      <Layers className="w-3.5 h-3.5 text-indigo-400" /> Multi-Agent Isolation Steps
                    </span>
                    <div className="space-y-1 text-slate-300 font-sans mt-1">
                      <p><strong className="text-rose-400">Root Cause Agent:</strong> {msg.structuredResponse.root_cause}</p>
                      <p><strong className="text-amber-400">Impact Agent:</strong> {msg.structuredResponse.business_impact}</p>
                      <p><strong className="text-cyan-400">Blast Radius Agent:</strong> {msg.structuredResponse.blast_radius}</p>
                    </div>
                  </div>

                  {/* Recommended Action Checklist */}
                  {msg.structuredResponse.recommended_actions && msg.structuredResponse.recommended_actions.length > 0 && (
                    <div className="space-y-1.5">
                      <span className="text-[10px] text-muted-foreground uppercase font-bold tracking-wider flex items-center gap-1">
                        <CheckCircle className="w-3.5 h-3.5 text-emerald-400" /> Recommended Action Commands
                      </span>
                      <div className="space-y-1 text-[10px] font-mono text-indigo-300 bg-slate-950 p-2 rounded-lg border border-white/5">
                        {msg.structuredResponse.recommended_actions.map((act, aIdx) => (
                          <div key={aIdx} className="flex gap-2">
                            <span>{aIdx + 1}.</span>
                            <span>{act}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Source citations */}
                  {msg.structuredResponse.references && msg.structuredResponse.references.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 items-center pt-1.5 border-t border-white/5">
                      <span className="text-[9px] text-muted-foreground flex items-center gap-0.5"><BookOpen className="w-3 h-3" /> Citations:</span>
                      {msg.structuredResponse.references.map((ref, rIdx) => (
                        <span key={rIdx} className="text-[8px] bg-slate-950 text-cyan-400 px-1.5 py-0.5 rounded border border-white/5 font-mono">
                          {ref}
                        </span>
                      ))}
                    </div>
                  )}

                </div>
              )}
            </div>
            <span className="text-[9px] text-muted-foreground/60 mt-1 font-mono">
              {msg.timestamp}
            </span>
          </div>
        ))}

        {/* Typing indicator / Streaming Status */}
        {statusMessage && (
          <div className="flex items-center gap-2 bg-slate-950/40 border border-white/5 rounded-xl p-3 text-xs text-muted-foreground w-fit animate-pulse">
            <RefreshCw className="w-3.5 h-3.5 animate-spin text-indigo-400" />
            <span>{statusMessage}</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Quick Prompts */}
      <div className="px-4 py-2 border-t border-white/5 bg-slate-950/20 flex gap-2 overflow-x-auto scrollbar-none">
        <button
          onClick={() => triggerPrompt("Is there a configuration drift alert active?")}
          className="flex-shrink-0 text-[10px] bg-slate-900 border border-white/5 hover:border-indigo-500/30 text-slate-300 px-2.5 py-1 rounded-full font-semibold transition-colors"
        >
          🔍 Compliance Drift
        </button>
        <button
          onClick={() => triggerPrompt("What happens if Mumbai Hub aggregator fails?")}
          className="flex-shrink-0 text-[10px] bg-slate-900 border border-white/5 hover:border-indigo-500/30 text-slate-300 px-2.5 py-1 rounded-full font-semibold transition-colors"
        >
          🎯 Outage Simulation
        </button>
        <button
          onClick={() => triggerPrompt("Show OSPF cost cost adjustments runbook manual")}
          className="flex-shrink-0 text-[10px] bg-slate-900 border border-white/5 hover:border-indigo-500/30 text-slate-300 px-2.5 py-1 rounded-full font-semibold transition-colors"
        >
          📖 OSPF Runbook
        </button>
      </div>

      {/* Input Form */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        className="p-3.5 border-t border-white/5 flex gap-2 bg-slate-900/20"
      >
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder="Ask Copilot (e.g. 'Show OSPF loop fix')..."
          className="flex-1 bg-slate-950/60 border border-white/5 rounded-xl px-4 py-2 text-xs sm:text-sm text-slate-100 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/20 transition-all font-sans"
        />
        <button
          type="submit"
          className="p-2.5 bg-indigo-600 hover:bg-indigo-500 rounded-xl text-white border border-indigo-500/20 transition-colors"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
};
