// Location: frontend/components/LogFeed.tsx
"use client";

import { ScrollArea } from "@/components/ui/scroll-area";
import { LogEntry } from "@/lib/types";
import { cn } from "@/lib/utils";

interface LogFeedProps {
    logs: LogEntry[];
}

const logTypeClasses: Record<LogEntry["log_type"], string> = {
    system: "text-blue-400",
    info: "text-muted-foreground",
    success: "text-green-500",
    fail: "text-yellow-500",
    error: "text-red-500",
};

export function LogFeed({ logs }: LogFeedProps) {
    return (
        <div className="h-full w-full bg-secondary text-secondary-foreground flex flex-col">
            <h3 className="text-lg font-semibold p-4 border-b">Live Log</h3>
            <ScrollArea className="flex-1 p-4">
                <div className="flex flex-col-reverse gap-2">
                    {logs.length === 0 && (
                        <p className="font-mono text-xs text-muted-foreground">
                            Waiting for log output...
                        </p>
                    )}
                    {logs.map((log) => (
                        <div
                            key={log.id}
                            className={cn("font-mono text-xs", logTypeClasses[log.log_type])}
                        >
              <span className="text-muted-foreground/50 mr-2">
                {log.timestamp}
              </span>
                            <span>{log.message}</span>
                        </div>
                    ))}
                </div>
            </ScrollArea>
        </div>
    );
}