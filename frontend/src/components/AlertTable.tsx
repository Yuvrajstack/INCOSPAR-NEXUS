import { ShieldAlert, CheckCircle2, ChevronRight } from "lucide-react";

export interface AlertItem {
  id: string;
  timestamp: string;
  device: string;
  title: string;
  severity: "critical" | "high" | "medium" | "low";
  description: string;
  confidenceScore: number;
  blastRadius: number; // Percentage
  status: "active" | "resolved";
  category: string;
}

interface AlertTableProps {
  alerts: AlertItem[];
  onSelectAlert: (alertId: string) => void;
  selectedAlertId: string | null;
}

export const AlertTable: React.FC<AlertTableProps> = ({
  alerts,
  onSelectAlert,
  selectedAlertId,
}) => {
  // Compute Risk Score
  const calculateRisk = () => {
    if (alerts.length === 0) return 4; // Low default
    const criticalCount = alerts.filter(a => a.severity === "critical").length;
    const highCount = alerts.filter(a => a.severity === "high").length;
    const mediumCount = alerts.filter(a => a.severity === "medium").length;

    let score = criticalCount * 35 + highCount * 18 + mediumCount * 8;
    return Math.min(score, 100);
  };

  const riskScore = calculateRisk();

  const getRiskLabel = (score: number) => {
    if (score > 80) return { label: "CRITICAL", color: "text-rose-500", bg: "bg-rose-500/10 border-rose-500/20" };
    if (score > 50) return { label: "HIGH RISK", color: "text-amber-500", bg: "bg-amber-500/10 border-amber-500/20" };
    if (score > 20) return { label: "MODERATE", color: "text-yellow-500", bg: "bg-yellow-500/10 border-yellow-500/20" };
    return { label: "STABLE", color: "text-emerald-500", bg: "bg-emerald-500/10 border-emerald-500/20" };
  };

  const riskMeta = getRiskLabel(riskScore);

  const getSeverityBadge = (sev: string) => {
    switch (sev) {
      case "critical":
        return "bg-rose-500/10 text-rose-400 border border-rose-500/20";
      case "high":
        return "bg-orange-500/10 text-orange-400 border border-orange-500/20";
      case "medium":
        return "bg-amber-500/10 text-amber-400 border border-amber-500/20";
      default:
        return "bg-slate-500/10 text-slate-400 border border-white/5";
    }
  };

  return (
    <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
      {/* Risk Meter Widget */}
      <div className="glass-panel p-5 rounded-xl flex flex-col justify-between border border-white/5 xl:col-span-1 shadow-xl">
        <div>
          <span className="text-xs text-muted-foreground uppercase font-bold tracking-wider">Security & Operations</span>
          <h3 className="text-lg font-bold text-slate-100 mt-0.5">NOC Risk Index</h3>
        </div>

        {/* Circular Gauge Ring representation */}
        <div className="flex flex-col items-center justify-center py-6">
          <div className="relative flex items-center justify-center">
            {/* SVG Arc Progress Ring */}
            <svg className="w-28 h-28 transform -rotate-90">
              <circle
                cx="56"
                cy="56"
                r="46"
                className="stroke-slate-900"
                strokeWidth="8"
                fill="none"
              />
              <circle
                cx="56"
                cy="56"
                r="46"
                className="transition-all duration-1000 ease-out"
                stroke={
                  riskScore > 80 ? "#ef4444" : riskScore > 50 ? "#f97316" : riskScore > 20 ? "#eab308" : "#10b981"
                }
                strokeWidth="8"
                fill="none"
                strokeDasharray="289"
                strokeDashoffset={289 - (289 * riskScore) / 100}
                strokeLinecap="round"
              />
            </svg>
            <div className="absolute text-center">
              <span className="text-3xl font-extrabold font-mono text-slate-100">{riskScore}</span>
              <span className="text-[10px] text-muted-foreground block font-bold mt-[-4px]">%</span>
            </div>
          </div>
          <span className={`mt-4 text-xs font-extrabold px-3 py-1 rounded-full border ${riskMeta.bg} ${riskMeta.color} tracking-widest`}>
            {riskMeta.label}
          </span>
        </div>

        <div className="pt-3 border-t border-white/5 grid grid-cols-2 gap-2 text-center text-xs">
          <div className="bg-slate-950/40 p-2 rounded-lg border border-white/5">
            <span className="text-muted-foreground block text-[10px]">Threat Blast</span>
            <span className="font-bold text-slate-200 mt-0.5 block">
              {alerts.length > 0 ? `${Math.max(...alerts.map(a => a.blastRadius))}%` : "0%"}
            </span>
          </div>
          <div className="bg-slate-950/40 p-2 rounded-lg border border-white/5">
            <span className="text-muted-foreground block text-[10px]">Active Issues</span>
            <span className="font-bold text-slate-200 mt-0.5 block font-mono">{alerts.length}</span>
          </div>
        </div>
      </div>

      {/* Alerts Table */}
      <div className="glass-panel rounded-xl overflow-hidden border border-white/5 xl:col-span-3 shadow-xl flex flex-col">
        <div className="px-5 py-4 border-b border-white/5 flex justify-between items-center bg-slate-900/20">
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-indigo-400" />
            <h3 className="font-bold text-slate-200">Autonomous AIOps Alert Prioritization</h3>
          </div>
          <span className="text-xs text-muted-foreground">Sorted by Severity & Influence</span>
        </div>

        <div className="flex-1 overflow-x-auto min-h-[220px]">
          <table className="w-full text-left border-collapse text-xs sm:text-sm">
            <thead>
              <tr className="border-b border-white/5 bg-slate-900/40 text-muted-foreground text-[10px] font-bold uppercase tracking-wider">
                <th className="py-3 px-4">Severity</th>
                <th className="py-3 px-4">Target Device</th>
                <th className="py-3 px-4">Alert Name</th>
                <th className="py-3 px-4 text-center">ML Confidence</th>
                <th className="py-3 px-4 text-center">Blast Radius</th>
                <th className="py-3 px-4">Timestamp</th>
                <th className="py-3 px-4">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {alerts.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-slate-400">
                    <div className="flex flex-col items-center justify-center gap-2">
                      <CheckCircle2 className="w-8 h-8 text-emerald-500 animate-pulse" />
                      <span className="font-bold text-slate-300">All Systems Nominal</span>
                      <span className="text-xs text-muted-foreground">Predictive models running at 100% SLA health.</span>
                    </div>
                  </td>
                </tr>
              ) : (
                alerts.map((alert) => (
                  <tr
                    key={alert.id}
                    onClick={() => onSelectAlert(alert.id)}
                    className={`cursor-pointer hover:bg-slate-900/35 transition-colors ${
                      selectedAlertId === alert.id ? "bg-indigo-600/10" : ""
                    }`}
                  >
                    <td className="py-3 px-4">
                      <span className={`px-2 py-0.5 rounded-full font-bold text-[9px] uppercase tracking-wider ${getSeverityBadge(alert.severity)}`}>
                        {alert.severity}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-semibold text-slate-300">{alert.device}</td>
                    <td className="py-3 px-4">
                      <div className="max-w-xs sm:max-w-md truncate">
                        <span className="font-medium text-slate-200">{alert.title}</span>
                        <span className="text-xs text-muted-foreground block truncate mt-0.5">
                          {alert.description}
                        </span>
                      </div>
                    </td>
                    <td className="py-3 px-4 text-center font-mono font-bold text-indigo-400">
                      {(alert.confidenceScore * 100).toFixed(0)}%
                    </td>
                    <td className="py-3 px-4 text-center font-mono text-slate-300">
                      <div className="flex items-center justify-center gap-1.5">
                        <span className="font-bold">{alert.blastRadius}%</span>
                        <div className="w-12 bg-slate-950 h-1.5 rounded-full overflow-hidden border border-white/5">
                          <div
                            className={`h-full ${
                              alert.blastRadius > 70 ? 'bg-rose-500' : alert.blastRadius > 40 ? 'bg-orange-500' : 'bg-yellow-500'
                            }`}
                            style={{ width: `${alert.blastRadius}%` }}
                          />
                        </div>
                      </div>
                    </td>
                    <td className="py-3 px-4 text-muted-foreground font-mono">{alert.timestamp}</td>
                    <td className="py-3 px-4 text-indigo-400 font-bold hover:text-indigo-300">
                      <div className="flex items-center gap-0.5">
                        Analyze <ChevronRight className="w-3.5 h-3.5" />
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
