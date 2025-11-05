// Location: frontend/components/LogFeed.tsx
"use client";

import { ScrollArea } from "@/components/ui/scroll-area";
import { LogEntry } from "@/lib/types";
import { cn } from "@/lib/utils";
import { Terminal, Activity, CheckCircle2, AlertTriangle, XCircle, Info } from "lucide-react";

interface LogFeedProps {
    logs: LogEntry[];
}

const logTypeConfig: Record<LogEntry["log_type"], { 
    color: string;
    bgColor: string;
    borderColor: string;
    icon: React.ComponentType<{ className?: string }>;
    label: string;
}> = {
    system: { 
        color: "text-blue-300", 
        bgColor: "bg-blue-500/10",
        borderColor: "border-l-blue-500",
        icon: Terminal,
        label: "SYSTEM"
    },
    info: { 
        color: "text-cyan-300", 
        bgColor: "bg-cyan-500/10",
        borderColor: "border-l-cyan-500",
        icon: Info,
        label: "INFO"
    },
    success: { 
        color: "text-green-300", 
        bgColor: "bg-green-500/10",
        borderColor: "border-l-green-500",
        icon: CheckCircle2,
        label: "SUCCESS"
    },
    fail: { 
        color: "text-yellow-300", 
        bgColor: "bg-yellow-500/10",
        borderColor: "border-l-yellow-500",
        icon: AlertTriangle,
        label: "WARN"
    },
    error: { 
        color: "text-red-300", 
        bgColor: "bg-red-500/10",
        borderColor: "border-l-red-500",
        icon: XCircle,
        label: "ERROR"
    },
};

export function LogFeed({ logs }: LogFeedProps) {
    return (
        <div className="h-full w-full bg-gradient-to-br from-gray-950 to-black text-white flex flex-col border border-white/10 rounded-lg overflow-hidden shadow-xl">
            {/* Header */}
            <div className="px-5 py-3.5 border-b border-white/10 bg-gradient-to-r from-gray-900/60 to-gray-900/40 backdrop-blur-sm">
                <div className="flex items-center gap-3">
                    <div className="p-1.5 rounded-md bg-indigo-500/20 border border-indigo-500/30">
                        <Activity className="h-3.5 w-3.5 text-indigo-400" />
                    </div>
                    <h3 className="text-sm font-semibold text-white">Live Logs</h3>
                    {logs.length > 0 && (
                        <div className="ml-auto flex items-center gap-2">
                            <div className="h-1.5 w-1.5 rounded-full bg-green-400 animate-pulse shadow-sm shadow-green-400/50"></div>
                            <span className="text-xs text-white/50 font-mono tabular-nums">
                                {logs.length}
                            </span>
                        </div>
                    )}
                </div>
            </div>
            
            {/* Logs Area */}
            <ScrollArea className="flex-1">
                <div className="flex flex-col-reverse gap-0.5 p-3">
                    {logs.length === 0 && (
                        <div className="flex flex-col items-center justify-center py-16 gap-3">
                            <div className="p-4 rounded-xl bg-white/5 border border-white/10">
                                <Terminal className="h-8 w-8 text-white/30" />
                            </div>
                            <div className="text-center">
                                <p className="text-sm text-white/60 font-medium mb-1">No logs yet</p>
                                <p className="font-mono text-xs text-white/40">
                                    Waiting for system output...
                                </p>
                            </div>
                        </div>
                    )}
                    {logs.map((log) => {
                        const config = logTypeConfig[log.log_type];
                        const Icon = config.icon;
                        
                        return (
                            <div
                                key={log.id}
                                className={cn(
                                    "group flex items-start gap-3 px-3 py-2.5 rounded-md border-l-2 transition-all hover:bg-white/5",
                                    config.bgColor,
                                    config.borderColor
                                )}
                            >
                                {/* Icon & Badge */}
                                <div className="flex items-center gap-2 pt-0.5">
                                    <Icon className={cn("h-3.5 w-3.5 flex-shrink-0", config.color)} />
                                    <span className={cn(
                                        "text-[9px] font-bold uppercase tracking-wider opacity-70",
                                        config.color
                                    )}>
                                        {config.label}
                                    </span>
                                </div>
                                
                                {/* Content */}
                                <div className="flex-1 min-w-0 space-y-1">
                                    <div className="font-mono text-[10px] text-white/40 tabular-nums">
                                        {log.timestamp}
                                    </div>
                                    <div className={cn(
                                        "font-mono text-xs leading-relaxed break-words",
                                        config.color
                                    )}>
                                        {log.message}
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            </ScrollArea>
        </div>
    );
}