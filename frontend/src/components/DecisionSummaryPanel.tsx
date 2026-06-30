import React, { useState } from "react";
import { Brain, HelpCircle, Users, Network, Cpu, Server, Play } from "lucide-react";

interface DecisionSummaryPanelProps {
  decision: any;
  rootCause: any;
  activeAnomaly: string | null;
}

export const DecisionSummaryPanel: React.FC<DecisionSummaryPanelProps> = ({
  decision,
  rootCause,
  activeAnomaly,
}) => {
  const [selectedSimNode, setSelectedSimNode] = useState("HUB-Mumbai");
  const [simResults, setSimResults] = useState<any>(null);
  const [simLoading, setSimLoading] = useState(false);

  const runWhatIfSimulation = async () => {
    setSimLoading(true);
    try {
      const res = await fetch("http://localhost:8000/api/simulate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ device_id: selectedSimNode })
      });
      if (res.ok) {
        const data = await res.json();
        setSimResults(data);
      }
    } catch (err) {
      console.error("Simulation failed:", err);
    } finally {
      setSimLoading(false);
    }
  };

  // Safe destructuring defaults
  const impact = decision?.business_impact || {};
  const blast = decision?.blast_radius_analysis || {};
  const confidence = decision?.decision_confidence || 1.0;
  const breakdown = decision?.confidence_breakdown || {
    telemetry_quality: 0.99,
    prediction_confidence: 1.0,
    graph_confidence: 0.95,
    historical_match: 0.0
  };

  return (
    <div className="space-y-6">
      {/* Overview & RCA grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* RCA & Summary Column (7 cols) */}
        <div className="lg:col-span-7 xl:col-span-8 space-y-6">
          
          {/* Decision Summary Card */}
          <div className="glass-panel p-5 rounded-xl border border-white/5 relative overflow-hidden shadow-xl flex gap-4">
            <div className="p-3 bg-indigo-500/10 border border-indigo-500/20 rounded-xl h-fit">
              <Brain className="w-6 h-6 text-indigo-400" />
            </div>
            <div className="flex-1">
              <div className="flex items-center justify-between flex-wrap gap-2">
                <span className="text-[10px] text-indigo-400 font-bold uppercase tracking-wider block font-mono">
                  AIOps Decision Summary
                </span>
                {decision?.recovery_priority && (
                  <span className={`text-[9px] px-2 py-0.5 rounded font-mono border ${
                    decision.recovery_priority.includes("P1")
                      ? "bg-rose-500/10 border-rose-500/20 text-rose-400"
                      : "bg-emerald-500/10 border-emerald-500/20 text-emerald-400"
                  }`}>
                    {decision.recovery_priority}
                  </span>
                )}
              </div>
              <h3 className="text-base font-bold text-slate-100 mt-1">
                {activeAnomaly ? "Dynamic Event Resolution State" : "Nominal System Alignment"}
              </h3>
              <p className="text-xs text-muted-foreground mt-2 leading-relaxed">
                {decision?.incident_summary || "Telemetry scans confirm all interfaces and overlay links match established baseline metrics."}
              </p>
              
              {activeAnomaly && (
                <div className="mt-4 pt-3 border-t border-white/5 grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                  <div>
                    <span className="text-muted-foreground font-semibold">Alternative Route:</span>
                    <p className="text-indigo-300 font-mono text-[11px] mt-0.5">{decision?.alternative_network_path}</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground font-semibold">Preventive Action:</span>
                    <p className="text-slate-300 text-[11px] mt-0.5">{decision?.preventive_recommendation}</p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Root Cause Analysis (RCA) Card */}
          <div className="glass-panel p-5 rounded-xl border border-white/5 shadow-xl">
            <div className="flex items-center gap-2 border-b border-white/5 pb-3 mb-4">
              <Cpu className="w-5 h-5 text-indigo-400" />
              <h3 className="font-bold text-slate-200 text-sm">Operator Root Cause Diagnostics</h3>
            </div>
            
            <div className="space-y-4">
              <div>
                <span className="text-[10px] text-muted-foreground uppercase font-bold tracking-wider">Isolated Primary Root Cause</span>
                <p className="text-sm font-bold text-rose-400 mt-0.5">
                  {rootCause?.primary_root_cause || "Inliers status. Operational telemetry reports healthy behavior parameters."}
                </p>
              </div>

              {rootCause?.supporting_evidence && rootCause.supporting_evidence.length > 0 && (
                <div>
                  <span className="text-[10px] text-muted-foreground uppercase font-bold tracking-wider">Supporting Evidence Signals</span>
                  <ul className="mt-1.5 space-y-1.5 text-xs text-slate-300">
                    {rootCause.supporting_evidence.map((ev: string, idx: number) => (
                      <li key={idx} className="flex items-start gap-2">
                        <span className="text-rose-400 font-bold">•</span>
                        <span>{ev}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {rootCause?.contributing_signals && rootCause.contributing_signals.length > 0 && (
                <div>
                  <span className="text-[10px] text-muted-foreground uppercase font-bold tracking-wider">Contributing Topology Events</span>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {rootCause.contributing_signals.map((sig: string, idx: number) => (
                      <span key={idx} className="text-[10px] bg-slate-950 px-2 py-1 border border-white/5 rounded text-slate-300">
                        {sig}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {rootCause?.dependency_chain && rootCause.dependency_chain.length > 0 && (
                <div>
                  <span className="text-[10px] text-muted-foreground uppercase font-bold tracking-wider">Device Dependency Chain Path</span>
                  <div className="flex items-center gap-2 mt-2 font-mono text-[10px] text-indigo-300 bg-slate-950/60 p-2.5 rounded-lg border border-white/5 overflow-x-auto">
                    {rootCause.dependency_chain.map((dev: string, idx: number) => (
                      <React.Fragment key={idx}>
                        <span className="flex items-center gap-1">
                          <Server className="w-3.5 h-3.5 text-slate-400" />
                          {dev}
                        </span>
                        {idx !== rootCause.dependency_chain.length - 1 && <span>&rarr;</span>}
                      </React.Fragment>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* SLA & Confidence Column (5 cols) */}
        <div className="lg:col-span-5 xl:col-span-4 space-y-6">
          {/* Decision Confidence Gauge Card */}
          <div className="glass-panel p-5 rounded-xl border border-white/5 shadow-xl flex flex-col justify-between h-full">
            <div>
              <div className="flex justify-between items-center mb-4">
                <h3 className="font-bold text-slate-200 text-sm">Decision Confidence</h3>
                <span className="text-[10px] text-indigo-400 font-mono font-bold">AIOPS-v4.0</span>
              </div>
              <div className="flex items-center gap-5 justify-center py-4 border-b border-white/5">
                <div className="relative w-24 h-24">
                  <svg className="w-full h-full" viewBox="0 0 100 100">
                    <circle className="text-slate-800" strokeWidth="6" stroke="currentColor" fill="transparent" r="40" cx="50" cy="50"/>
                    <circle className="text-indigo-500" strokeWidth="6" strokeDasharray="251.2" strokeDashoffset={251.2 - (confidence * 251.2)} strokeLinecap="round" stroke="currentColor" fill="transparent" r="40" cx="50" cy="50"/>
                  </svg>
                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <span className="text-lg font-extrabold text-slate-200 font-mono">{(confidence * 100).toFixed(0)}%</span>
                    <span className="text-[8px] text-muted-foreground font-bold">CONFIDENCE</span>
                  </div>
                </div>

                <div className="space-y-1.5 text-[11px] text-slate-300 font-mono flex-1">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Telemetry Quality:</span>
                    <span className="text-emerald-400">{(breakdown.telemetry_quality * 100).toFixed(0)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">ML Predictor:</span>
                    <span className="text-indigo-400">{(breakdown.prediction_confidence * 100).toFixed(0)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Graph Topology:</span>
                    <span className="text-cyan-400">{(breakdown.graph_confidence * 100).toFixed(0)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">KB Match:</span>
                    <span className={breakdown.historical_match > 0 ? "text-indigo-400" : "text-slate-500"}>
                      {breakdown.historical_match > 0 ? `${(breakdown.historical_match * 100).toFixed(0)}%` : "N/A"}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <div className="pt-4 text-xs text-muted-foreground leading-relaxed flex items-start gap-2">
              <HelpCircle className="w-4 h-4 text-slate-500 flex-shrink-0" />
              <span>
                Calculated based on temporal z-score telemetry offsets, OSPF route link weights, and active incident template records.
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Impact & Blast Radius and Timeline */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* Business Impact Card */}
        <div className="glass-panel p-5 rounded-xl border border-white/5 shadow-xl space-y-4">
          <div className="flex items-center gap-2 border-b border-white/5 pb-3">
            <Users className="w-5 h-5 text-indigo-400" />
            <h3 className="font-bold text-slate-200 text-sm">Business & SLA Impact Matrix</h3>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-slate-950/40 p-3 rounded-lg border border-white/5">
              <span className="text-[10px] text-muted-foreground font-bold uppercase">Estimated Users Impacted</span>
              <p className="text-lg font-bold font-mono text-slate-200 mt-0.5">
                {impact.estimated_users_impacted || 0} users
              </p>
            </div>
            <div className="bg-slate-950/40 p-3 rounded-lg border border-white/5">
              <span className="text-[10px] text-muted-foreground font-bold uppercase">SLA Breach Risk</span>
              <p className={`text-lg font-bold font-mono mt-0.5 ${
                (impact.sla_impact || 0) > 70 ? "text-rose-400 animate-pulse" : (impact.sla_impact || 0) > 30 ? "text-amber-400" : "text-emerald-400"
              }`}>
                {(impact.sla_impact || 0).toFixed(0)}%
              </p>
            </div>
            <div className="bg-slate-950/40 p-3 rounded-lg border border-white/5">
              <span className="text-[10px] text-muted-foreground font-bold uppercase">Estimated MTTR Downtime</span>
              <p className="text-lg font-bold font-mono text-slate-200 mt-0.5">
                {impact.estimated_downtime_minutes || 0} mins
              </p>
            </div>
            <div className="bg-slate-950/40 p-3 rounded-lg border border-white/5">
              <span className="text-[10px] text-muted-foreground font-bold uppercase">Severity Category</span>
              <p className={`text-lg font-bold font-mono mt-0.5 ${
                impact.operational_severity === "CRITICAL" ? "text-rose-500" : impact.operational_severity === "HIGH" ? "text-rose-400" : impact.operational_severity === "MEDIUM" ? "text-amber-400" : "text-emerald-400"
              }`}>
                {impact.operational_severity || "LOW"}
              </p>
            </div>
          </div>

          {impact.affected_services && impact.affected_services.length > 0 && (
            <div className="pt-2">
              <span className="text-[10px] text-muted-foreground font-bold uppercase">Degraded Systems & Services</span>
              <div className="flex flex-wrap gap-2 mt-1.5">
                {impact.affected_services.map((srv: string, idx: number) => (
                  <span key={idx} className="text-[10px] bg-indigo-500/10 border border-indigo-500/20 px-2 py-0.5 rounded font-mono text-indigo-300">
                    {srv}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Dynamic Blast Radius Card */}
        <div className="glass-panel p-5 rounded-xl border border-white/5 shadow-xl space-y-4">
          <div className="flex items-center gap-2 border-b border-white/5 pb-3">
            <Network className="w-5 h-5 text-indigo-400" />
            <h3 className="font-bold text-slate-200 text-sm">Dynamic Topological Blast Radius</h3>
          </div>

          <div className="flex items-center gap-4">
            <div className="w-20 h-20 flex-shrink-0 relative">
              <svg className="w-full h-full" viewBox="0 0 100 100">
                <circle className="text-slate-800" strokeWidth="5" stroke="currentColor" fill="transparent" r="40" cx="50" cy="50"/>
                <circle className="text-rose-500" strokeWidth="5" strokeDasharray="251.2" strokeDashoffset={251.2 - ((blast.blast_radius_percent || 0.0) / 100 * 251.2)} strokeLinecap="round" stroke="currentColor" fill="transparent" r="40" cx="50" cy="50"/>
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-sm font-extrabold text-slate-200 font-mono">{(blast.blast_radius_percent || 0).toFixed(0)}%</span>
              </div>
            </div>

            <div className="flex-1 space-y-1.5 text-xs">
              <div className="flex justify-between">
                <span className="text-muted-foreground font-semibold">Immediate:</span>
                <span className="text-slate-200">{blast.immediate_impact || "None"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground font-semibold">Upstream:</span>
                <span className="text-slate-200">{blast.upstream_impact || "None"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground font-semibold">Downstream:</span>
                <span className="text-slate-200">{blast.downstream_impact || "None"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground font-semibold">Propagation Path:</span>
                <span className="text-indigo-400 font-mono text-[10px] truncate max-w-[200px]">{blast.service_propagation_path || "N/A"}</span>
              </div>
            </div>
          </div>

          {blast.critical_dependencies && blast.critical_dependencies.length > 0 && (
            <div className="pt-2">
              <span className="text-[10px] text-muted-foreground font-bold uppercase">Aggregator Dependencies</span>
              <div className="flex flex-wrap gap-2 mt-1.5 text-[10px] font-mono">
                {blast.critical_dependencies.map((dep: string, idx: number) => (
                  <span key={idx} className="bg-slate-950 px-2 py-0.5 border border-white/5 rounded text-cyan-400">
                    {dep}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* What-If Outage Simulator Card */}
      <div className="glass-panel p-5 rounded-xl border border-white/5 shadow-xl space-y-4">
        <div className="flex items-center gap-2 border-b border-white/5 pb-3">
          <HelpCircle className="w-5 h-5 text-indigo-400" />
          <h3 className="font-bold text-slate-200 text-sm">Interactive What-If Outage Simulation</h3>
        </div>

        <div className="flex flex-col sm:flex-row gap-4 items-end">
          <div className="flex-1 space-y-1.5">
            <label className="text-[10px] text-muted-foreground uppercase font-bold tracking-wider">Select Device Outage Target</label>
            <select
              value={selectedSimNode}
              onChange={(e) => setSelectedSimNode(e.target.value)}
              className="w-full bg-slate-950 border border-white/10 rounded-lg px-3 py-2 text-xs font-mono text-slate-200 focus:outline-none focus:border-indigo-500"
            >
              <option value="DC-Bangalore">Bangalore DC (Core)</option>
              <option value="HUB-Mumbai">Mumbai Hub (Transit Aggregator)</option>
              <option value="BR-Delhi">New Delhi Branch (BR-1)</option>
              <option value="BR-Kolkata">Kolkata Branch (BR-2)</option>
              <option value="BR-Chennai">Chennai Branch (BR-3)</option>
              <option value="BR-Hyderabad">Hyderabad Branch (BR-4)</option>
            </select>
          </div>
          
          <button
            onClick={runWhatIfSimulation}
            disabled={simLoading}
            className="w-full sm:w-auto flex items-center justify-center gap-2 text-xs bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 text-white font-semibold px-5 py-2.5 rounded-lg transition-colors border border-indigo-500/20"
          >
            <Play className="w-4 h-4" />
            {simLoading ? "Modeling Outage..." : "Predict Outage Impact"}
          </button>
        </div>

        {simResults && (
          <div className="bg-slate-950/60 border border-white/5 rounded-xl p-4 space-y-3 font-sans text-xs">
            <div className="flex justify-between items-center pb-2 border-b border-white/5">
              <span className="font-bold text-rose-400">Simulation Forecast: Failure on {simResults.device_id}</span>
              <span className="text-[9px] bg-rose-500/10 text-rose-400 border border-rose-500/20 px-2 py-0.5 rounded font-mono">
                Outage Scenario
              </span>
            </div>
            
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="space-y-1">
                <span className="text-muted-foreground">Topological Blast Radius:</span>
                <p className="font-mono font-bold text-slate-200">{simResults.blast_radius_percent.toFixed(0)}%</p>
              </div>
              <div className="space-y-1">
                <span className="text-muted-foreground">Estimated Downtime:</span>
                <p className="font-mono font-bold text-slate-200">{simResults.predicted_downtime_minutes} minutes</p>
              </div>
              <div className="space-y-1">
                <span className="text-muted-foreground">Affected Users Count:</span>
                <p className="font-mono font-bold text-slate-200">{simResults.estimated_users_impacted}</p>
              </div>
            </div>

            <div className="space-y-1">
              <span className="text-muted-foreground font-semibold">Affected Services:</span>
              <div className="flex flex-wrap gap-1.5 mt-1 font-mono text-[9px]">
                {simResults.affected_services.map((srv: string, idx: number) => (
                  <span key={idx} className="bg-slate-900 border border-white/5 px-2 py-0.5 rounded text-indigo-300">
                    {srv}
                  </span>
                ))}
              </div>
            </div>

            <div className="space-y-1 pt-1.5 border-t border-white/5">
              <span className="text-muted-foreground font-semibold">Remediation Rerouting Action:</span>
              <p className="text-slate-300 mt-0.5">{simResults.recommended_rerouting}</p>
            </div>
          </div>
        )}
      </div>

    </div>
  );
};
