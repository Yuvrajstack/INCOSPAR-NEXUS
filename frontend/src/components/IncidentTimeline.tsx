import React from "react";
import { Terminal, ShieldAlert, CheckCircle, RefreshCw, AlertCircle } from "lucide-react";

export interface TimelineEvent {
  id: string;
  time: string;
  type: "anomaly" | "playbook" | "syslog" | "recovery";
  title: string;
  description: string;
  device?: string;
}

interface IncidentTimelineProps {
  events: TimelineEvent[];
}

export const IncidentTimeline: React.FC<IncidentTimelineProps> = ({ events }) => {
  const getIcon = (type: string) => {
    switch (type) {
      case "anomaly":
        return (
          <div className="p-1.5 bg-rose-500/10 border border-rose-500/30 rounded-lg text-rose-400">
            <ShieldAlert className="w-4 h-4" />
          </div>
        );
      case "playbook":
        return (
          <div className="p-1.5 bg-indigo-500/10 border border-indigo-500/30 rounded-lg text-indigo-400">
            <Terminal className="w-4 h-4" />
          </div>
        );
      case "syslog":
        return (
          <div className="p-1.5 bg-amber-500/10 border border-amber-500/30 rounded-lg text-amber-400">
            <AlertCircle className="w-4 h-4" />
          </div>
        );
      case "recovery":
        return (
          <div className="p-1.5 bg-emerald-500/10 border border-emerald-500/30 rounded-lg text-emerald-400">
            <CheckCircle className="w-4 h-4" />
          </div>
        );
      default:
        return (
          <div className="p-1.5 bg-slate-500/10 border border-white/5 rounded-lg text-slate-400">
            <RefreshCw className="w-4 h-4" />
          </div>
        );
    }
  };

  return (
    <div className="glass-panel p-5 rounded-xl border border-white/5 shadow-xl flex flex-col h-[520px]">
      <div className="flex items-center gap-2 mb-4 border-b border-white/5 pb-3">
        <RefreshCw className="w-4 h-4 text-indigo-400" />
        <h3 className="font-bold text-slate-200">Incident & Autonomic History</h3>
      </div>

      <div className="flex-1 overflow-y-auto pr-1 space-y-4 scrollbar-thin">
        {events.length === 0 ? (
          <p className="text-xs text-muted-foreground text-center py-12">No event records found.</p>
        ) : (
          events.map((event, idx) => (
            <div key={event.id || idx} className="flex gap-4 relative group">
              {/* Timeline Connector Line */}
              {idx !== events.length - 1 && (
                <span
                  className="absolute left-[17px] top-[30px] bottom-[-20px] w-[2px] bg-slate-800"
                  aria-hidden="true"
                />
              )}

              {/* Event Icon */}
              <div className="z-10 flex-shrink-0">{getIcon(event.type)}</div>

              {/* Event Content */}
              <div className="flex-1 bg-slate-900/30 group-hover:bg-slate-900/50 transition-all p-3 rounded-lg border border-white/5">
                <div className="flex justify-between items-start gap-2 mb-1">
                  <h4 className="font-bold text-xs sm:text-sm text-slate-200">
                    {event.title}
                  </h4>
                  <span className="text-[10px] text-muted-foreground font-mono bg-slate-950 px-1.5 py-0.5 rounded border border-white/5">
                    {event.time}
                  </span>
                </div>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  {event.description}
                </p>
                {event.device && (
                  <span className="inline-block mt-2 text-[9px] bg-slate-950 font-mono text-indigo-400 border border-indigo-500/10 px-1.5 py-0.5 rounded">
                    Device: {event.device}
                  </span>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
