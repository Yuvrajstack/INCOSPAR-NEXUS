import { useState, useEffect, useRef } from "react";
import {
  Activity,
  CheckCircle,
  AlertTriangle,
  Zap,
  TrendingUp,
  Cpu,
  Brain,
} from "lucide-react";
import { type Edge, type Node } from "reactflow";
import { DigitalTwin, type NodeData } from "./components/DigitalTwin";
import { NetworkCharts } from "./components/NetworkCharts";
import { CopilotChat } from "./components/CopilotChat";
import { AlertTable, type AlertItem } from "./components/AlertTable";
import { IncidentTimeline, type TimelineEvent } from "./components/IncidentTimeline";
import { DecisionSummaryPanel } from "./components/DecisionSummaryPanel";
import { PlaybookRemediationPanel } from "./components/PlaybookRemediationPanel";


// Helper to generate time string
const getTimeString = (offsetSeconds = 0) => {
  const d = new Date();
  if (offsetSeconds) d.setSeconds(d.getSeconds() + offsetSeconds);
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
};

const API_BASE = "http://localhost:8000/api";
const WS_BASE = "ws://localhost:8000";

// Initial Nodes
const initialNodes: Node<NodeData>[] = [
  {
    id: "DC-Bangalore",
    type: "routerNode",
    position: { x: 280, y: 30 },
    data: { name: "Bangalore DC (Core)", ip: "10.10.0.1", type: "DC", status: "healthy", cpu: 14, memory: 42 },
  },
  {
    id: "HUB-Mumbai",
    type: "routerNode",
    position: { x: 280, y: 170 },
    data: { name: "Mumbai Hub (Transit)", ip: "10.20.0.1", type: "Hub", status: "healthy", cpu: 18, memory: 35 },
  },
  {
    id: "BR-Delhi",
    type: "routerNode",
    position: { x: 40, y: 320 },
    data: { name: "New Delhi Branch (BR-1)", ip: "10.30.1.1", type: "Branch", status: "healthy", cpu: 8, memory: 24 },
  },
  {
    id: "BR-Kolkata",
    type: "routerNode",
    position: { x: 280, y: 320 },
    data: { name: "Kolkata Branch (BR-2)", ip: "10.30.2.1", type: "Branch", status: "healthy", cpu: 11, memory: 28 },
  },
  {
    id: "BR-Chennai",
    type: "routerNode",
    position: { x: 520, y: 320 },
    data: { name: "Chennai Branch (BR-3)", ip: "10.30.3.1", type: "Branch", status: "healthy", cpu: 15, memory: 31 },
  },
  {
    id: "BR-Hyderabad",
    type: "routerNode",
    position: { x: 760, y: 320 },
    data: { name: "Hyderabad Branch (BR-4)", ip: "10.30.4.1", type: "Branch", status: "healthy", cpu: 12, memory: 29 },
  },
];

// Initial Edges
const initialEdges: Edge[] = [
  {
    id: "L-DC-HUB",
    source: "DC-Bangalore",
    target: "HUB-Mumbai",
    label: "MPLS Core (1Gbps)",
    animated: true,
    style: { stroke: "#10b981", strokeWidth: 3 },
  },
  {
    id: "L-HUB-BR1",
    source: "HUB-Mumbai",
    target: "BR-Delhi",
    label: "IPSec overlay",
    animated: true,
    style: { stroke: "#10b981", strokeWidth: 2, strokeDasharray: "5, 5" },
  },
  {
    id: "L-HUB-BR2",
    source: "HUB-Mumbai",
    target: "BR-Kolkata",
    label: "IPSec overlay",
    animated: true,
    style: { stroke: "#10b981", strokeWidth: 2, strokeDasharray: "5, 5" },
  },
  {
    id: "L-HUB-BR3",
    source: "HUB-Mumbai",
    target: "BR-Chennai",
    label: "IPSec overlay",
    animated: true,
    style: { stroke: "#10b981", strokeWidth: 2, strokeDasharray: "5, 5" },
  },
  {
    id: "L-HUB-BR4",
    source: "HUB-Mumbai",
    target: "BR-Hyderabad",
    label: "IPSec overlay",
    animated: true,
    style: { stroke: "#10b981", strokeWidth: 2, strokeDasharray: "5, 5" },
  },
];

export default function App() {
  const [nodes, setNodes] = useState<Node<NodeData>[]>(initialNodes);
  const [edges, setEdges] = useState<Edge[]>(initialEdges);
  const [activeAnomaly, setActiveAnomaly] = useState<string | null>(null);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [timelineEvents, setTimelineEvents] = useState<TimelineEvent[]>([
    {
      id: "init",
      time: getTimeString(-120),
      type: "recovery",
      title: "NOC Monitor Initialized",
      description: "Air-gapped SD-WAN control center established. Normal state active.",
    },
  ]);
  const [activeDashboardTab, setActiveDashboardTab] = useState<"noc" | "aiops">("noc");
  const [rootCause, setRootCause] = useState<any>(null);
  const [decisionSummary, setDecisionSummary] = useState<any>(null);

  const [historyData, setHistoryData] = useState<any[]>([]);
  const [selectedElement, setSelectedElement] = useState<{
    type: "node" | "link";
    id: string;
    name: string;
  } | null>(null);

  // Playbook execution simulation
  const [playbookRunning, setPlaybookRunning] = useState(false);
  const [playbookLogs, setPlaybookLogs] = useState<string[]>([]);
  const logIntervalRef = useRef<any>(null);

  // Keep selectedElement reference in a ref so the WS message handler doesn't cause reconnects
  const selectedElementRef = useRef(selectedElement);
  useEffect(() => {
    selectedElementRef.current = selectedElement;
  }, [selectedElement]);

  // Fetch initial history on mount or when selectedElement changes
  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const currentSelected = selectedElementRef.current;
        const targetId = currentSelected?.type === "node" ? currentSelected.id : "DC-Bangalore";
        const res = await fetch(`${API_BASE}/history?device_id=${targetId}&limit=15`);
        if (res.ok) {
          const data = await res.json();
          // Backend history is returned descending (latest first). Reverse to display oldest first.
          const formatted = data.reverse().map((item: any) => ({
            time: new Date(item.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" }),
            throughput: item.rx_bandwidth,
            latency: item.latency,
            packetLoss: item.packet_loss,
            cpu: item.cpu_usage
          }));
          setHistoryData(formatted);
        }
      } catch (err) {
        console.error("Failed to fetch telemetry history:", err);
      }
    };
    fetchHistory();
  }, [selectedElement]);

  // Update React Flow nodes metrics whenever device list is updated
  const updateNodesFromDevices = (devicesList: any[]) => {
    setNodes((prevNodes) =>
      prevNodes.map((node) => {
        const dev = devicesList.find((d) => d.id === node.id);
        if (!dev) return node;
        return {
          ...node,
          data: {
            ...node.data,
            status: dev.status,
            cpu: dev.cpu_usage,
            memory: dev.memory_usage,
            name: dev.name,
            ip: dev.ip_address,
          },
        };
      })
    );
  };

  // Helper to handle incoming telemetry frames from WebSocket
  const handleTelemetryFrame = (payload: any) => {
    const { devices, alerts: wsAlerts, logs: wsLogs, active_anomaly, root_cause, decision_summary, incident_timeline } = payload;
    
    // Update active nodes
    updateNodesFromDevices(devices);
    
    // Update active anomaly
    setActiveAnomaly(active_anomaly);

    // Update Phase 4 states
    setRootCause(root_cause || null);
    setDecisionSummary(decision_summary || null);

    // Update active alerts list
    const mappedAlerts: AlertItem[] = wsAlerts.map((a: any) => {
      let severity: AlertItem["severity"] = "low";
      if (a.severity === "warning") severity = "medium";
      if (a.severity === "critical") severity = "high";
      if (a.severity === "emergency") severity = "critical";

      let blast = 30;
      if (a.severity === "critical") blast = 60;
      if (a.severity === "emergency") blast = 100;

      return {
        id: a.id,
        timestamp: new Date(a.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" }),
        device: a.device_id,
        title: a.title,
        severity,
        description: a.description,
        confidenceScore: a.confidence,
        blastRadius: blast,
        status: a.status,
        category: a.title.includes("IPSec") ? "Security" : a.title.includes("OSPF") || a.title.includes("BGP") ? "Routing" : "Congestion"
      };
    });
    setAlerts(mappedAlerts);

    // Update timeline logs (either from incident timeline or fallback logs)
    if (incident_timeline && incident_timeline.length > 0) {
      const mappedTimeline: TimelineEvent[] = incident_timeline.map((item: any, idx: number) => {
        let type: TimelineEvent["type"] = "syslog";
        if (item.event_type === "alarm") type = "anomaly";
        else if (item.event_type === "playbook") type = "playbook";
        else if (item.event_type === "rca") type = "recovery";
        return {
          id: `timeline-${idx}-${item.time}`,
          time: item.time,
          type,
          title: item.title,
          description: item.description,
          device: root_cause?.device_id || undefined
        };
      });
      setTimelineEvents(mappedTimeline);
    } else {
      const mappedEvents: TimelineEvent[] = wsLogs.map((log: any, idx: number) => {
        let type: "syslog" | "anomaly" | "recovery" = "syslog";
        if (log.message.includes("INJECTED")) {
          type = "anomaly";
        } else if (log.message.includes("self-healing") || log.message.includes("finalized") || log.message.includes("SUCCESS")) {
          type = "recovery";
        }
        return {
          id: `log-${idx}-${log.timestamp}`,
          time: new Date(log.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" }),
          type,
          title: `${log.protocol || "SYS"} - ${log.severity}`,
          description: log.message,
          device: log.device_id
        };
      });
      setTimelineEvents(mappedEvents);
    }


    // Append a new real-time history point
    setHistoryData((prev) => {
      const nextTime = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
      const nextData = [...prev];
      if (nextData.length >= 15) {
        nextData.shift();
      }

      // Read from currently selected element, or fallback to Bangalore DC
      const currentSelected = selectedElementRef.current;
      const targetId = currentSelected?.type === "node" ? currentSelected.id : "DC-Bangalore";
      const targetDev = devices.find((d: any) => d.id === targetId) || devices[0];

      if (targetDev) {
        nextData.push({
          time: nextTime,
          throughput: targetDev.rx_bandwidth || 0,
          latency: targetDev.latency || 0,
          packetLoss: targetDev.packet_loss || 0,
          cpu: targetDev.cpu_usage || 0
        });
      }
      return nextData;
    });
  };

  // WebSocket telemetry subscription connection setup with auto-reconnect
  useEffect(() => {
    let socket: WebSocket | null = null;
    let reconnectTimeout: any = null;

    const connectWS = () => {
      console.log("Connecting to WebSocket telemetry stream...");
      socket = new WebSocket(`${WS_BASE}/ws/telemetry`);

      socket.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          handleTelemetryFrame(payload);
        } catch (err) {
          console.error("Error parsing telemetry frame:", err);
        }
      };

      socket.onclose = () => {
        console.log("WebSocket connection closed. Retrying in 3 seconds...");
        reconnectTimeout = setTimeout(connectWS, 3000);
      };

      socket.onerror = (error) => {
        console.error("WebSocket error:", error);
        socket?.close();
      };
    };

    connectWS();

    return () => {
      if (socket) {
        socket.onclose = null;
        socket.close();
      }
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
      }
    };
  }, []);

  // Update React Flow edges styles reactively whenever activeAnomaly changes
  useEffect(() => {
    const updatedEdges = initialEdges.map((edge) => {
      let color = "#10b981"; // Healthy green
      let width = edge.id === "L-DC-HUB" ? 3 : 2;
      let dash = edge.id === "L-DC-HUB" ? undefined : "5, 5";
      let animated = true;

      if (activeAnomaly === "CONGESTION_BR3" && edge.id === "L-HUB-BR3") {
        color = "#f59e0b"; // Warning orange
        width = 4;
        dash = "2, 2";
      } else if (activeAnomaly === "TUNNEL_BR1_DOWN" && edge.id === "L-HUB-BR1") {
        color = "#ef4444"; // Critical red
        width = 3;
        dash = undefined;
        animated = false;
      } else if (activeAnomaly === "IPSEC_DEGRADED" && edge.id === "L-HUB-BR1") {
        color = "#f59e0b"; // Warning orange
        width = 3;
        dash = "1, 5";
      } else if (activeAnomaly === "ROUTING_LOOP_HUB" && edge.id === "L-DC-HUB") {
        color = "#ef4444"; // Loop red
        width = 4;
        animated = false;
      } else if (activeAnomaly === "CONFIG_DRIFT" && edge.id === "L-HUB-BR2") {
        color = "#f59e0b"; // MTU mismatch warning
        width = 3;
        dash = "2, 2";
      } else if (activeAnomaly === "INTERFACE_FAIL" && edge.id === "L-HUB-BR4") {
        color = "#ef4444"; // Port link failure
        width = 3;
        dash = undefined;
        animated = false;
      } else if (activeAnomaly === "BGP_FLAP" && edge.id === "L-HUB-BR2") {
        color = "#f59e0b";
        width = 3;
        dash = "1, 5";
      }

      return {
        ...edge,
        animated,
        style: { stroke: color, strokeWidth: width, strokeDasharray: dash },
      };
    });
    setEdges(updatedEdges);
  }, [activeAnomaly]);

  // Handle selected elements changes
  const handleSelectElement = (type: "node" | "link", id: string) => {
    let name = "";
    if (type === "node") {
      name = nodes.find((n) => n.id === id)?.data.name || id;
    } else {
      const label = edges.find((e) => e.id === id)?.label;
      name = typeof label === "string" ? label : id;
    }
    setSelectedElement({ type, id, name });
  };

  // Inject Anomaly REST API Handler
  const handleInjectAnomaly = async (anomalyType: string) => {
    if (playbookRunning) return;
    try {
      const res = await fetch(`${API_BASE}/inject-fault`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scenario: anomalyType })
      });
      if (!res.ok) {
        console.error("Failed to inject anomaly:", await res.text());
      }
    } catch (err) {
      console.error("Network error when injecting anomaly:", err);
    }
  };

  // Reset Simulation REST API Handler
  const handleResetSimulation = async () => {
    if (playbookRunning) return;
    try {
      const res = await fetch(`${API_BASE}/recover`, {
        method: "POST"
      });
      if (!res.ok) {
        console.error("Failed to reset network:", await res.text());
      }
    } catch (err) {
      console.error("Network error when resetting network:", err);
    }
  };

  // Execute Playbook Sequence (UI Console logs, followed by real recovery API dispatch)
  const handleExecutePlaybook = (playbookId: string) => {
    if (playbookRunning) return;
    setPlaybookRunning(true);
    setPlaybookLogs(["Initializing Autonomic Action..."]);

    const scripts: Record<string, string[]> = {
      PB_QOS_ADJUST: [
        "Connecting to router BR-3 CLI via secure air-gapped SSH...",
        "Querying bandwidth interface statistics...",
        "Executing command: 'configure terminal; policy-map SDWAN-SHAPER'...",
        "Assigning Class priority 1 to Real-time application traffic...",
        "Executing: 'class class-default; police rate 85000000 conform-action transmit exceed-action drop'...",
        "Verifying queue congestion level...",
        "Throughput stabilized: 82.5 Mbps. Loss returning to 0.01%.",
        "SUCCESS: Traffic bandwidth shaped and priorities adjusted.",
      ],
      PB_IPSEC_RESTART: [
        "Connecting to New Delhi Branch Router-1 (BR-1)...",
        "Flushing cryptographic security associations (SA)...",
        "Running command: 'clear crypto isakmp; clear crypto ipsec sa'...",
        "Initiating dynamic Phase 1 IKE keys rekeying...",
        "Negotiating Diffie-Hellman Group 14 handshakes...",
        "Syslog check: IPSec tunnel session ESTABLISHED.",
        "Restarting local OSPF daemon routing interface...",
        "OSPF Neighbor state changed: LOADING -> FULL.",
        "SUCCESS: IPSec Tunnel and OSPF peer convergence complete.",
      ],
      PB_RESET_METRICS: [
        "Connecting to transit aggregator Hub-1...",
        "Executing loop mitigation verification scripts...",
        "Adjusting cost metric on link L-DC-HUB interface...",
        "Command: 'router ospf 100; interface gig0/1; ip ospf cost 40'...",
        "Route tables flushed and re-converged...",
        "CPU load returning to baseline (14% usage).",
        "SUCCESS: Route routing loop corrected. Performance normalized.",
      ],
      PB_REKEY_HARDEN: [
        "Isolating IP network segment on BR-2 WAN interfaces...",
        "Deploying ACL filtering rules script...",
        "Applying command: 'ip access-list extended SEC-HARDEN; deny ip 198.51.100.0/24 any'...",
        "Performing security rotation of VPN Pre-Shared Keys...",
        "Confirming data packet validation checks...",
        "Packet integrity verified. Anti-replay error cleared.",
        "SUCCESS: ACL applied and IPSec tunnel secured.",
      ],
    };

    const logs = scripts[playbookId] || ["Running custom diagnostics...", "No action required.", "SUCCESS."];
    let logIndex = 0;

    logIntervalRef.current = setInterval(() => {
      if (logIndex < logs.length) {
        setPlaybookLogs((prev) => [...prev, logs[logIndex]]);
        logIndex++;
      } else {
        clearInterval(logIntervalRef.current!);
        setPlaybookRunning(false);
        handleResetSimulation(); // Call backend to recover!
      }
    }, 1500);
  };

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col font-sans selection:bg-indigo-500/30 selection:text-white">
      {/* Top Banner Navigation Header */}
      <header className="px-6 py-4 border-b border-white/5 bg-slate-900/60 backdrop-blur-md sticky top-0 z-50 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-indigo-600/20 border border-indigo-500/30 rounded-xl">
            <Zap className="w-6 h-6 text-indigo-400 animate-pulse-slow" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg sm:text-xl font-extrabold tracking-tight bg-gradient-to-r from-indigo-200 via-indigo-400 to-cyan-400 bg-clip-text text-transparent">
                Incospar Nexus AI
              </h1>
              <span className="text-[9px] bg-slate-950 px-2 py-0.5 border border-white/5 rounded font-mono text-cyan-400">
                HACKATHON-v1.0
              </span>
            </div>
            <p className="text-[10px] sm:text-xs text-muted-foreground font-medium">
              Autonomous SD-WAN Digital Twin & Predictive AIOps Copilot
            </p>
          </div>
        </div>

        {/* Global SLA KPI Dashboard Bar */}
        <div className="hidden lg:flex items-center gap-6 text-xs border-l border-white/5 pl-6">
          <div className="flex flex-col">
            <span className="text-muted-foreground text-[10px] uppercase font-bold tracking-wider">Network SLA</span>
            <span className="font-bold text-emerald-400 mt-0.5 font-mono text-sm">
              {activeAnomaly ? (activeAnomaly === "ROUTING_LOOP_HUB" ? "92.40%" : "97.85%") : "99.98%"}
            </span>
          </div>
          <div className="flex flex-col">
            <span className="text-muted-foreground text-[10px] uppercase font-bold tracking-wider">OSPF Uptime</span>
            <span className="font-bold text-slate-200 mt-0.5 font-mono text-sm">18d 4h 12m</span>
          </div>
          <div className="flex flex-col">
            <span className="text-muted-foreground text-[10px] uppercase font-bold tracking-wider">Active Tunnels</span>
            <span className="font-bold text-slate-200 mt-0.5 font-mono text-sm">
              {activeAnomaly === "TUNNEL_BR1_DOWN" || activeAnomaly === "INTERFACE_FAIL" ? "3 / 4" : "4 / 4"}
            </span>
          </div>
          <div className="flex flex-col">
            <span className="text-muted-foreground text-[10px] uppercase font-bold tracking-wider">System State</span>
            <span className="font-bold text-slate-200 mt-0.5 flex items-center gap-1.5 font-mono text-sm">
              {activeAnomaly ? (
                <span className="text-rose-400 flex items-center gap-1">
                  <AlertTriangle className="w-4 h-4 animate-bounce" /> Warning
                </span>
              ) : (
                <span className="text-emerald-400 flex items-center gap-1">
                  <CheckCircle className="w-4 h-4" /> Healthy
                </span>
              )}
            </span>
          </div>
        </div>
      </header>

      {/* Main Container Layout */}
      <main className="flex-1 p-6 space-y-6 max-w-[1600px] mx-auto w-full font-sans">
        
        {/* Navigation Tabs */}
        <div className="flex items-center gap-4 border-b border-white/5 pb-3">
          <button
            onClick={() => setActiveDashboardTab("noc")}
            className={`px-4 py-2.5 text-xs sm:text-sm font-semibold rounded-xl border transition-all duration-300 ${
              activeDashboardTab === "noc"
                ? "bg-indigo-600 border-indigo-500/30 text-white shadow-lg shadow-indigo-600/10"
                : "bg-slate-950/40 hover:bg-slate-800/80 border-white/5 text-slate-400 hover:text-slate-200"
            }`}
          >
            NOC Monitor Overview
          </button>
          <button
            onClick={() => setActiveDashboardTab("aiops")}
            className={`px-4 py-2.5 text-xs sm:text-sm font-semibold rounded-xl border transition-all duration-300 flex items-center gap-2 ${
              activeDashboardTab === "aiops"
                ? "bg-indigo-600 border-indigo-500/30 text-white shadow-lg shadow-indigo-600/10"
                : "bg-slate-950/40 hover:bg-slate-800/80 border-white/5 text-slate-400 hover:text-slate-200"
            }`}
          >
            <Brain className="w-4 h-4 text-slate-100" />
            AIOps Decision Intelligence Engine
          </button>
        </div>

        {activeDashboardTab === "noc" ? (
          <>
            {/* ML Prediction Cards row */}
            <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Prediction Card 1: LSTM */}
              <div className="glass-panel p-5 rounded-xl border border-white/5 relative overflow-hidden shadow-xl flex gap-4">
                <div className="p-3 bg-indigo-500/10 border border-indigo-500/20 rounded-xl h-fit">
                  <TrendingUp className="w-6 h-6 text-indigo-400" />
                </div>
                <div>
                  <span className="text-[10px] text-indigo-400 font-bold uppercase tracking-wider block font-mono">
                    LSTM Forecast Engine
                  </span>
                  <h4 className="text-base font-bold text-slate-200 mt-0.5">Time-to-Impact Congestion</h4>
                  <p className="text-xs text-muted-foreground mt-1 leading-relaxed">
                    {activeAnomaly === "CONGESTION_BR3" ? (
                      <span className="text-rose-400 font-semibold block animate-pulse">
                        ⚠️ CRITICAL: Saturation forecasted in 4 minutes (98% probability). Degradation severity: High.
                      </span>
                    ) : (
                      "Telemetry forecasts bandwidth trends for the next 15 minutes. Currently, all tunnels are within safe usage parameters (<40%)."
                    )}
                  </p>
                </div>
              </div>

              {/* Prediction Card 2: XGBoost */}
              <div className="glass-panel p-5 rounded-xl border border-white/5 relative overflow-hidden shadow-xl flex gap-4">
                <div className="p-3 bg-cyan-500/10 border border-cyan-500/20 rounded-xl h-fit">
                  <Cpu className="w-6 h-6 text-cyan-400" />
                </div>
                <div>
                  <span className="text-[10px] text-cyan-400 font-bold uppercase tracking-wider block font-mono">
                    XGBoost Tunnel Assessment
                  </span>
                  <h4 className="text-base font-bold text-slate-200 mt-0.5">Tunnel Health Classification</h4>
                  <p className="text-xs text-muted-foreground mt-1 leading-relaxed">
                    {activeAnomaly === "TUNNEL_BR1_DOWN" ? (
                      <span className="text-rose-400 font-semibold block">
                        ❌ FAILED: BR-1 IPSec overlay classified as DOWN (99% confidence). Key negotiation failure detected.
                      </span>
                    ) : activeAnomaly === "IPSEC_DEGRADED" ? (
                      <span className="text-amber-400 font-semibold block">
                        ⚠️ DEGRADED: BR-1 tunnel experiencing 15.4% loss. XGBoost anomaly probability: 93%.
                      </span>
                    ) : activeAnomaly === "CONFIG_DRIFT" ? (
                      <span className="text-amber-400 font-semibold block">
                        ⚠️ ANOMALY: BR-2 interface experiencing MTU drift configuration mismatch warnings.
                      </span>
                    ) : (
                      "Continuously evaluating packet headers, keepalives, and latency deviations. All overlays classified: STABLE (99.8% SLA score)."
                    )}
                  </p>
                </div>
              </div>

              {/* Prediction Card 3: Isolation Forest */}
              <div className="glass-panel p-5 rounded-xl border border-white/5 relative overflow-hidden shadow-xl flex gap-4">
                <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-xl h-fit">
                  <Activity className="w-6 h-6 text-emerald-400" />
                </div>
                <div>
                  <span className="text-[10px] text-emerald-400 font-bold uppercase tracking-wider block font-mono">
                    Isolation Forest Check
                  </span>
                  <h4 className="text-base font-bold text-slate-200 mt-0.5">Micro-variate Telemetry Check</h4>
                  <p className="text-xs text-muted-foreground mt-1 leading-relaxed">
                    {activeAnomaly === "ROUTING_LOOP_HUB" ? (
                      <span className="text-rose-400 font-semibold block">
                        ⚠️ OUTLIER: Detected multivariate routing anomalies on Hub-1. CPU usage vs. route convergence rates mismatch.
                      </span>
                    ) : activeAnomaly === "INTERFACE_FAIL" ? (
                      <span className="text-rose-400 font-semibold block animate-pulse">
                        ⚠️ CRITICAL: BR-4 (Hyderabad) interface failure detected. Link state: DOWN.
                      </span>
                    ) : (
                      "Analyzing high-dimensional SNMP telemetry (CPU, RAM, packets) for outlier signatures. Current state: NOMINAL (Inlier score: 0.94)."
                    )}
                  </p>
                </div>
              </div>
            </section>

            {/* Digital Twin & Copilot Side-by-Side */}
            <section className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              {/* Digital Twin Network Map (8 columns) */}
              <div className="lg:col-span-7 xl:col-span-8">
                <DigitalTwin
                  nodes={nodes}
                  edges={edges}
                  onElementSelect={handleSelectElement}
                  onInjectAnomaly={handleInjectAnomaly}
                  onResetSimulation={handleResetSimulation}
                  activeAnomaly={activeAnomaly}
                />
              </div>

              {/* AI NOC Copilot Sidebar (4 columns) */}
              <div className="lg:col-span-5 xl:col-span-4">
                <CopilotChat
                  playbookLogs={playbookLogs}
                />
              </div>
            </section>

            {/* Live Recharts Telemetry Section */}
            <section>
              <NetworkCharts historyData={historyData} selectedElement={selectedElement} />
            </section>

            {/* AIOps Alert Prioritization and Timeline Section */}
            <section className="grid grid-cols-1 lg:grid-cols-4 gap-6">
              {/* Alerts center (3 columns) */}
              <div className="lg:col-span-3">
                <AlertTable
                  alerts={alerts}
                  onSelectAlert={(id) => {
                    const alertItem = alerts.find((a) => a.id === id);
                    if (alertItem) {
                      setSelectedElement({ type: "node", id: alertItem.device.includes("BR-3") ? "BR-3" : alertItem.device.includes("BR-1") ? "BR-1" : "HUB-1", name: alertItem.device });
                    }
                  }}
                  selectedAlertId={alerts.length > 0 ? alerts[0].id : null}
                />
              </div>

              {/* Vertical Events Timeline (1 column) */}
              <div className="lg:col-span-1">
                <IncidentTimeline events={timelineEvents} />
              </div>
            </section>
          </>
        ) : (
          <div className="space-y-6 animate-fade-in">
            <DecisionSummaryPanel
              decision={decisionSummary}
              rootCause={rootCause}
              activeAnomaly={activeAnomaly}
            />
            
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              <div className="lg:col-span-8">
                <PlaybookRemediationPanel
                  playbook={decisionSummary?.playbook}
                  kbMatch={decisionSummary?.historical_match}
                  onExecutePlaybook={handleExecutePlaybook}
                  playbookRunning={playbookRunning}
                  playbookLogs={playbookLogs}
                />
              </div>
              <div className="lg:col-span-4">
                <IncidentTimeline events={timelineEvents} />
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer copyright */}
      <footer className="mt-12 py-6 border-t border-white/5 bg-slate-950/80 text-center text-xs text-muted-foreground font-mono">
        <p>© 2026 ISRO Bharatiya Antariksh Hackathon - Incospar Nexus AI. All rights reserved.</p>
        <p className="mt-1.5 text-[10px] text-muted-foreground/50">Air-Gapped Autonomous Operation Mode Only.</p>
      </footer>
    </div>
  );
}
