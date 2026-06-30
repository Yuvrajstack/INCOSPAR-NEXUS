import React from "react";
import { Terminal, ShieldAlert, CheckCircle, Clock, BookOpen, Sparkles, RefreshCw } from "lucide-react";

interface PlaybookRemediationPanelProps {
  playbook: any;
  kbMatch: any;
  onExecutePlaybook: (playbookId: string) => void;
  playbookRunning: boolean;
  playbookLogs: string[];
}

export const PlaybookRemediationPanel: React.FC<PlaybookRemediationPanelProps> = ({
  playbook,
  kbMatch,
  onExecutePlaybook,
  playbookRunning,
  playbookLogs,
}) => {
  const steps = playbook?.remediation_steps || ["No active failures. Default baseline policy active."];

  return (
    <div className="space-y-6">
      
      {/* Dynamic Remediation steps panel */}
      <div className="glass-panel p-5 rounded-xl border border-white/5 shadow-xl space-y-4">
        
        <div className="flex justify-between items-center flex-wrap gap-3 border-b border-white/5 pb-3">
          <div className="flex items-center gap-2">
            <Terminal className="w-5 h-5 text-indigo-400" />
            <h3 className="font-bold text-slate-200 text-sm">Autonomic Remediation Playbook</h3>
          </div>
          {playbook?.playbook_id && playbook.playbook_id !== "PB_NONE" && (
            <button
              onClick={() => onExecutePlaybook(playbook.playbook_id)}
              disabled={playbookRunning}
              className="text-xs bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 text-white font-semibold px-4 py-2 rounded-lg transition-colors border border-indigo-500/20 flex items-center gap-1.5"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${playbookRunning ? 'animate-spin' : ''}`} />
              {playbookRunning ? "Executing Autonomic Actions..." : "Execute Remediation Playbook"}
            </button>
          )}
        </div>

        <div className="space-y-3">
          <div>
            <span className="text-[10px] text-muted-foreground uppercase font-bold tracking-wider">Playbook Policy Identifier</span>
            <p className="text-sm font-bold text-slate-200 mt-0.5">
              {playbook?.playbook_name || "Standard NOC Monitoring Blueprint"}
            </p>
          </div>

          <div>
            <span className="text-[10px] text-muted-foreground uppercase font-bold tracking-wider">Autonomic Execution Steps</span>
            <div className="mt-2 space-y-2 font-mono text-xs">
              {steps.map((step: string, idx: number) => (
                <div key={idx} className="flex gap-3 bg-slate-950/40 p-2.5 rounded-lg border border-white/5 items-start">
                  <span className="text-indigo-400 font-bold">0{idx + 1}.</span>
                  <span className="text-slate-300">{step}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Playbook console logs if running */}
        {playbookRunning && (
          <div className="bg-slate-950 border border-white/10 rounded-lg p-4 font-mono text-[11px] text-emerald-400 space-y-1.5 shadow-inner">
            <div className="flex items-center justify-between pb-1.5 border-b border-white/5 mb-1.5 text-[9px] text-slate-500">
              <span className="flex items-center gap-1">❯ Remote Connection Console</span>
              <span className="animate-pulse">ONLINE</span>
            </div>
            {playbookLogs.map((log, index) => (
              <p key={index} className="leading-tight">
                {log.startsWith("SUCCESS") ? (
                  <span className="text-emerald-300 font-bold">✓ {log}</span>
                ) : log.startsWith("ERROR") ? (
                  <span className="text-rose-400 font-bold">✗ {log}</span>
                ) : (
                  <span>❯ {log}</span>
                )}
              </p>
            ))}
          </div>
        )}
      </div>

      {/* SLA / Remdiation Forecasts grid */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
        <div className="glass-panel p-4 rounded-xl border border-white/5 shadow-md space-y-1">
          <div className="flex items-center gap-1.5 text-slate-400 text-xs font-semibold">
            <Clock className="w-4 h-4 text-indigo-400" />
            <span>Remediation Timing</span>
          </div>
          <p className="text-base font-extrabold text-slate-200 font-mono">
            {playbook?.estimated_execution_time_seconds ? `${playbook.estimated_execution_time_seconds} seconds` : "N/A"}
          </p>
        </div>

        <div className="glass-panel p-4 rounded-xl border border-white/5 shadow-md space-y-1">
          <div className="flex items-center gap-1.5 text-slate-400 text-xs font-semibold">
            <Sparkles className="w-4 h-4 text-emerald-400" />
            <span>Expected Improvement</span>
          </div>
          <p className="text-xs text-slate-300 leading-normal">
            {playbook?.expected_improvement || "Stable baseline maintained."}
          </p>
        </div>

        <div className="glass-panel p-4 rounded-xl border border-white/5 shadow-md space-y-1">
          <div className="flex items-center gap-1.5 text-slate-400 text-xs font-semibold">
            <ShieldAlert className="w-4 h-4 text-rose-400" />
            <span>Risk of Inaction</span>
          </div>
          <p className="text-xs text-rose-300 leading-normal">
            {playbook?.risk_if_ignored || "Minimal risk."}
          </p>
        </div>
      </div>

      {/* Historical matches details from Knowledge Repository */}
      <div className="glass-panel p-5 rounded-xl border border-white/5 shadow-xl space-y-3">
        <div className="flex items-center gap-2 border-b border-white/5 pb-3 mb-2">
          <BookOpen className="w-5 h-5 text-indigo-400" />
          <h3 className="font-bold text-slate-200 text-sm">Resolved Incident Knowledge Base Matches</h3>
        </div>

        {kbMatch ? (
          <div className="flex gap-4">
            <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-xl h-fit flex-shrink-0">
              <CheckCircle className="w-6 h-6 text-emerald-400" />
            </div>
            <div className="space-y-1 text-xs">
              <span className="text-[10px] text-emerald-400 font-mono font-bold block">
                SIMILAR INCIDENT DETECTED &bull; MATCH STABILITY {(kbMatch.similarity_score * 100).toFixed(0)}%
              </span>
              <h4 className="text-sm font-bold text-slate-200">Historical Knowledge Record: {kbMatch.kb_id}</h4>
              <p className="text-slate-300 leading-relaxed mt-1">
                A similar outage occurred on <span className="font-mono text-slate-200">{kbMatch.resolved_at}</span>. The incident was successfully recovered by invoking Playbook <span className="font-mono text-indigo-400">{kbMatch.remediation}</span>.
              </p>
              <div className="pt-2">
                <span className="text-muted-foreground font-semibold">Resolution Summary:</span>
                <p className="text-slate-400 italic mt-0.5">{kbMatch.resolution_summary}</p>
              </div>
            </div>
          </div>
        ) : (
          <div className="text-xs text-muted-foreground py-4 text-center">
            No similar historical incident matches found in air-gapped knowledge database.
          </div>
        )}
      </div>

    </div>
  );
};
