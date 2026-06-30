import React, { useMemo } from "react";
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  Handle,
  Position,
  type NodeProps,
  type Edge,
  type Node,
} from "reactflow";
import "reactflow/dist/style.css";
import { Server, ShieldAlert, Network, ArrowRightLeft, Radio, AlertTriangle } from "lucide-react";

// Types
export interface NodeData {
  name: string;
  ip: string;
  type: "DC" | "Hub" | "Branch";
  status: "healthy" | "warning" | "critical";
  cpu: number;
  memory: number;
}

export interface LinkData {
  id: string;
  source: string;
  target: string;
  type: "MPLS" | "IPSec" | "Public";
  status: "up" | "degraded" | "down";
  bandwidth: number;
  throughput: number;
  latency: number;
  packetLoss: number;
}

// Custom Node Component
const DeviceNode: React.FC<NodeProps<NodeData>> = ({ data, selected }) => {
  const getIcon = () => {
    switch (data.type) {
      case "DC":
        return <Server className="w-5 h-5 text-indigo-400" />;
      case "Hub":
        return <Network className="w-5 h-5 text-cyan-400" />;
      case "Branch":
        return <Radio className="w-5 h-5 text-slate-400" />;
    }
  };

  const getStatusBorder = () => {
    if (selected) return "border-indigo-500 shadow-[0_0_12px_rgba(99,102,241,0.5)]";
    switch (data.status) {
      case "healthy":
        return "border-emerald-500/30 hover:border-emerald-500/60";
      case "warning":
        return "border-amber-500/40 hover:border-amber-500/70";
      case "critical":
        return "border-rose-500/50 hover:border-rose-500/80";
    }
  };

  const getStatusDot = () => {
    switch (data.status) {
      case "healthy":
        return <span className="absolute top-2 right-2 flex h-2 w-2"><span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span><span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span></span>;
      case "warning":
        return <span className="absolute top-2 right-2 flex h-2 w-2"><span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span><span className="relative inline-flex rounded-full h-2 w-2 bg-amber-500"></span></span>;
      case "critical":
        return <span className="absolute top-2 right-2 flex h-2 w-2"><span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75"></span><span className="relative inline-flex rounded-full h-2 w-2 bg-rose-500"></span></span>;
    }
  };

  return (
    <div className={`relative px-4 py-3 rounded-xl glass-panel border ${getStatusBorder()} transition-all duration-300 w-52 text-left`}>
      {getStatusDot()}
      <Handle type="target" position={Position.Top} className="!bg-indigo-500" />
      
      <div className="flex items-center gap-3">
        <div className="p-2 bg-slate-950/60 rounded-lg border border-white/5">
          {getIcon()}
        </div>
        <div className="min-w-0">
          <h4 className="font-bold text-sm text-slate-100 truncate">{data.name}</h4>
          <p className="text-xs text-muted-foreground font-mono">{data.ip}</p>
        </div>
      </div>

      <div className="mt-3 grid grid-cols-2 gap-2 pt-2 border-t border-white/5 text-[10px]">
        <div>
          <span className="text-muted-foreground">CPU: </span>
          <span className={`font-semibold font-mono ${data.cpu > 80 ? 'text-rose-400' : data.cpu > 50 ? 'text-amber-400' : 'text-emerald-400'}`}>
            {data.cpu.toFixed(0)}%
          </span>
        </div>
        <div>
          <span className="text-muted-foreground">RAM: </span>
          <span className="font-semibold font-mono text-slate-200">
            {data.memory.toFixed(0)}%
          </span>
        </div>
      </div>

      <Handle type="source" position={Position.Bottom} className="!bg-indigo-500" />
    </div>
  );
};

interface DigitalTwinProps {
  nodes: Node<NodeData>[];
  edges: Edge[];
  onElementSelect: (type: "node" | "link", id: string) => void;
  onInjectAnomaly: (type: string) => void;
  onResetSimulation: () => void;
  activeAnomaly: string | null;
}

export const DigitalTwin: React.FC<DigitalTwinProps> = ({
  nodes,
  edges,
  onElementSelect,
  onInjectAnomaly,
  onResetSimulation,
  activeAnomaly,
}) => {
  const nodeTypes = useMemo(() => ({ routerNode: DeviceNode }), []);

  const onNodeClick = (_event: React.MouseEvent, node: Node) => {
    onElementSelect("node", node.id);
  };

  const onEdgeClick = (_event: React.MouseEvent, edge: Edge) => {
    onElementSelect("link", edge.id);
  };

  return (
    <div className="glass-panel rounded-xl overflow-hidden flex flex-col h-[520px] relative border border-white/5 shadow-2xl">
      {/* Header Bar */}
      <div className="px-5 py-3 border-b border-white/5 flex justify-between items-center bg-slate-900/40 backdrop-blur-sm z-10">
        <div className="flex items-center gap-2">
          <Network className="w-5 h-5 text-indigo-400" />
          <h2 className="font-bold text-slate-200">Autonomous SD-WAN Digital Twin</h2>
        </div>
        <div className="flex items-center gap-3">
          {activeAnomaly && (
            <span className="text-[11px] bg-rose-500/10 text-rose-400 border border-rose-500/20 px-3 py-1 rounded-full font-semibold flex items-center gap-1.5 animate-pulse">
              <AlertTriangle className="w-3.5 h-3.5" /> Anomaly Injected: {activeAnomaly}
            </span>
          )}
          <button
            onClick={onResetSimulation}
            className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold px-3 py-1.5 rounded-lg border border-white/10 transition-colors"
          >
            Reset Twin State
          </button>
        </div>
      </div>

      {/* React Flow Workspace */}
      <div className="flex-1 min-h-0 bg-[#030712]/70 relative">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          onNodeClick={onNodeClick}
          onEdgeClick={onEdgeClick}
          fitView
          fitViewOptions={{ padding: 0.15 }}
          className="react-flow-nexus"
        >
          <Background color="#1e293b" gap={20} size={1} />
          <Controls className="!bg-slate-900 !border-white/10 !text-slate-200" />
          <MiniMap
            maskColor="rgba(2, 6, 23, 0.7)"
            nodeColor="#334155"
            className="!bg-slate-950/80 !border-white/10 !rounded-lg"
          />
        </ReactFlow>
      </div>

      {/* Control Panel Footer for Anomaly Injections */}
      <div className="p-4 border-t border-white/5 bg-slate-900/30 backdrop-blur-sm grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-2 z-10">
        <button
          onClick={() => onInjectAnomaly("CONGESTION_BR3")}
          className={`flex items-center justify-center gap-1 text-[10px] sm:text-xs font-semibold py-2 px-2 rounded-lg border transition-all duration-300 ${
            activeAnomaly === "CONGESTION_BR3"
              ? "bg-rose-500 border-rose-600 text-white"
              : "bg-slate-950/60 hover:bg-slate-800/80 border-white/5 text-slate-300 hover:text-slate-100"
          }`}
        >
          <ShieldAlert className="w-3.5 h-3.5 text-amber-500" />
          Congest BR-3
        </button>
        <button
          onClick={() => onInjectAnomaly("TUNNEL_BR1_DOWN")}
          className={`flex items-center justify-center gap-1 text-[10px] sm:text-xs font-semibold py-2 px-2 rounded-lg border transition-all duration-300 ${
            activeAnomaly === "TUNNEL_BR1_DOWN"
              ? "bg-rose-500 border-rose-600 text-white"
              : "bg-slate-950/60 hover:bg-slate-800/80 border-white/5 text-slate-300 hover:text-slate-100"
          }`}
        >
          <ShieldAlert className="w-3.5 h-3.5 text-rose-500" />
          Drop Tunnel BR-1
        </button>
        <button
          onClick={() => onInjectAnomaly("ROUTING_LOOP_HUB")}
          className={`flex items-center justify-center gap-1 text-[10px] sm:text-xs font-semibold py-2 px-2 rounded-lg border transition-all duration-300 ${
            activeAnomaly === "ROUTING_LOOP_HUB"
              ? "bg-rose-500 border-rose-600 text-white"
              : "bg-slate-950/60 hover:bg-slate-800/80 border-white/5 text-slate-300 hover:text-slate-100"
          }`}
        >
          <ArrowRightLeft className="w-3.5 h-3.5 text-indigo-400" />
          OSPF Loop Hub
        </button>
        <button
          onClick={() => onInjectAnomaly("IPSEC_DEGRADED")}
          className={`flex items-center justify-center gap-1 text-[10px] sm:text-xs font-semibold py-2 px-2 rounded-lg border transition-all duration-300 ${
            activeAnomaly === "IPSEC_DEGRADED"
              ? "bg-rose-500 border-rose-600 text-white"
              : "bg-slate-950/60 hover:bg-slate-800/80 border-white/5 text-slate-300 hover:text-slate-100"
          }`}
        >
          <AlertTriangle className="w-3.5 h-3.5 text-yellow-500" />
          Degrade IPSec BR-1
        </button>
        <button
          onClick={() => onInjectAnomaly("CONFIG_DRIFT")}
          className={`flex items-center justify-center gap-1 text-[10px] sm:text-xs font-semibold py-2 px-2 rounded-lg border transition-all duration-300 ${
            activeAnomaly === "CONFIG_DRIFT"
              ? "bg-rose-500 border-rose-600 text-white"
              : "bg-slate-950/60 hover:bg-slate-800/80 border-white/5 text-slate-300 hover:text-slate-100"
          }`}
        >
          <Server className="w-3.5 h-3.5 text-teal-400" />
          Drift MTU BR-2
        </button>
        <button
          onClick={() => onInjectAnomaly("INTERFACE_FAIL")}
          className={`flex items-center justify-center gap-1 text-[10px] sm:text-xs font-semibold py-2 px-2 rounded-lg border transition-all duration-300 ${
            activeAnomaly === "INTERFACE_FAIL"
              ? "bg-rose-500 border-rose-600 text-white"
              : "bg-slate-950/60 hover:bg-slate-800/80 border-white/5 text-slate-300 hover:text-slate-100"
          }`}
        >
          <Radio className="w-3.5 h-3.5 text-red-400 animate-pulse" />
          Fail Link BR-4
        </button>
        <button
          onClick={() => onInjectAnomaly("BGP_FLAP")}
          className={`flex items-center justify-center gap-1 text-[10px] sm:text-xs font-semibold py-2 px-2 rounded-lg border transition-all duration-300 ${
            activeAnomaly === "BGP_FLAP"
              ? "bg-rose-500 border-rose-600 text-white"
              : "bg-slate-950/60 hover:bg-slate-800/80 border-white/5 text-slate-300 hover:text-slate-100"
          }`}
        >
          <Network className="w-3.5 h-3.5 text-cyan-400" />
          Flap BGP Hub
        </button>
      </div>
    </div>
  );
};
