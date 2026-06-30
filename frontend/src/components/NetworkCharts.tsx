import React from "react";
import {
  AreaChart,
  Area,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
} from "recharts";

interface TelemetryData {
  time: string;
  throughput: number;
  latency: number;
  packetLoss: number;
  cpu: number;
}

interface NetworkChartsProps {
  historyData: TelemetryData[];
  selectedElement: { type: "node" | "link"; id: string; name: string } | null;
}

export const NetworkCharts: React.FC<NetworkChartsProps> = ({
  historyData,
  selectedElement,
}) => {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* SLA / Throughput Graph */}
      <div className="glass-panel p-5 rounded-xl flex flex-col h-[280px]">
        <div className="flex justify-between items-center mb-4">
          <div>
            <span className="text-xs text-muted-foreground uppercase font-bold tracking-wider">
              {selectedElement ? `${selectedElement.name} Throughput` : "Network Traffic Load"}
            </span>
            <h3 className="text-lg font-bold text-slate-100">
              {selectedElement ? "Real-time Bandwidth" : "Aggregate NetFlow"}
            </h3>
          </div>
          <span className="text-xs bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 px-2 py-0.5 rounded-full font-semibold">
            Live
          </span>
        </div>
        <div className="flex-1 w-full min-h-0">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={historyData} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="colorThroughput" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis
                dataKey="time"
                stroke="#64748b"
                fontSize={10}
                tickLine={false}
              />
              <YAxis
                stroke="#64748b"
                fontSize={10}
                tickLine={false}
                axisLine={false}
                unit="M"
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#0f172a",
                  borderColor: "rgba(99, 102, 241, 0.2)",
                  color: "#f8fafc",
                  borderRadius: "8px",
                  fontSize: "12px",
                }}
              />
              <Area
                type="monotone"
                dataKey="throughput"
                stroke="#6366f1"
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#colorThroughput)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Latency Graph */}
      <div className="glass-panel p-5 rounded-xl flex flex-col h-[280px]">
        <div className="flex justify-between items-center mb-4">
          <div>
            <span className="text-xs text-muted-foreground uppercase font-bold tracking-wider">
              {selectedElement ? `${selectedElement.name} Latency` : "Core Routing RTT"}
            </span>
            <h3 className="text-lg font-bold text-slate-100">Latency Profile</h3>
          </div>
          <span className="text-xs bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 px-2 py-0.5 rounded-full font-semibold">
            ms
          </span>
        </div>
        <div className="flex-1 w-full min-h-0">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={historyData} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis
                dataKey="time"
                stroke="#64748b"
                fontSize={10}
                tickLine={false}
              />
              <YAxis
                stroke="#64748b"
                fontSize={10}
                tickLine={false}
                axisLine={false}
                unit="ms"
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#0f172a",
                  borderColor: "rgba(6, 182, 212, 0.2)",
                  color: "#f8fafc",
                  borderRadius: "8px",
                  fontSize: "12px",
                }}
              />
              <Line
                type="monotone"
                dataKey="latency"
                stroke="#0ea5e9"
                strokeWidth={2.5}
                dot={false}
                activeDot={{ r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Packet Loss Graph */}
      <div className="glass-panel p-5 rounded-xl flex flex-col h-[280px]">
        <div className="flex justify-between items-center mb-4">
          <div>
            <span className="text-xs text-muted-foreground uppercase font-bold tracking-wider">
              {selectedElement ? `${selectedElement.name} Dropped` : "IPSec / MPLS Frame Loss"}
            </span>
            <h3 className="text-lg font-bold text-slate-100">Packet Loss Rate</h3>
          </div>
          <span className="text-xs bg-rose-500/10 text-rose-400 border border-rose-500/20 px-2 py-0.5 rounded-full font-semibold">
            %
          </span>
        </div>
        <div className="flex-1 w-full min-h-0">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={historyData} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis
                dataKey="time"
                stroke="#64748b"
                fontSize={10}
                tickLine={false}
              />
              <YAxis
                stroke="#64748b"
                fontSize={10}
                tickLine={false}
                axisLine={false}
                unit="%"
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#0f172a",
                  borderColor: "rgba(244, 63, 94, 0.2)",
                  color: "#f8fafc",
                  borderRadius: "8px",
                  fontSize: "12px",
                }}
              />
              <Bar
                dataKey="packetLoss"
                fill="#f43f5e"
                radius={[4, 4, 0, 0]}
                maxBarSize={20}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};
