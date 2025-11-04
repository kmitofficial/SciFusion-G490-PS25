// Location: frontend/app/app/experiment/[job_id]/page.tsx
"use client";

import { useState, useCallback, useMemo } from "react";
import { useParams } from "next/navigation";
import { useWebSocket } from "@/hooks/useWebSocket";
import {
    LogEntry,
    PaperBank,
    Idea,
    ExperimentResult,
    GroupedExperiment,
} from "@/lib/types";
import { useToast } from "@/hooks/use-toast";
import { LogFeed } from "@/components/LogFeed";
import { PaperCard } from "@/components/PaperCard"; // We still use this
import { JobProgressBar } from "@/components/JobProgressBar";
import { GroupedExperimentCard } from "@/components/GroupedExperimentCard";
import { Loader } from "lucide-react";

export default function ExperimentPage() {
    const params = useParams();
    const { toast } = useToast();
    const jobId = Array.isArray(params.job_id) ? params.job_id[0] : params.job_id;

    // --- State Management from your Sample ---
    const [logFeed, setLogFeed] = useState<LogEntry[]>([]);
    const [papers, setPapers] = useState<PaperBank | null>(null);
    const [baselineScore, setBaselineScore] = useState<number | null>(null);
    const [novelIdeas, setNovelIdeas] = useState<Idea[]>([]);
    const [totalExperiments, setTotalExperiments] = useState(0);
    const [allRunResults, setAllRunResults] = useState<ExperimentResult[]>([]);
    const [jobStatus, setJobStatus] = useState("running");
    // ---

    // Helper to add logs, ensuring most recent is at the top
    const addLog = useCallback(
        (message: string, log_type: LogEntry["log_type"] = "system") => {
            const newLog: LogEntry = {
                id: crypto.randomUUID(),
                message,
                log_type,
                timestamp: new Date().toLocaleTimeString(),
            };
            // Add to the start of the array
            setLogFeed((prevLogs) => [newLog, ...prevLogs.slice(0, 200)]);
        },
        [],
    );

    const handleMessage = useCallback(
        (message: any) => {
            const { type, data } = message;

            switch (type) {
                case "JOB_STATUS_UPDATE":
                    setJobStatus(data.status);
                    if (data.status === "complete" || data.status === "failed") {
                        addLog(`Job ${data.status}.`, "success");
                    }
                    break;

                case "AIDER_LOG":
                    addLog(data.message, data.log_type);
                    break;

                case "PAPERS_UPDATED":
                    setPapers(data as PaperBank);
                    addLog("Research papers have been collected.", "info");
                    // Attempt to find a baseline score
                    // THIS IS A GUESS. Your backend must send this.
                    const baseline =
                        data.baseline_score || 0.9105; // Fallback to your sample
                    setBaselineScore(baseline);
                    addLog(`Baseline score set to: ${baseline.toFixed(4)}`, "system");
                    break;

                // This is the initial list, which we don't use for cards
                case "IDEAS_UPDATED":
                    addLog(`Generated ${data.length} initial ideas.`, "info");
                    break;

                // This is the FINAL list of ideas to run
                case "NOVEL_IDEAS_UPDATED":
                    const novel: Idea[] = data;
                    addLog(
                        `Novelty check complete. ${novel.length} ideas will be run.`,
                        "success",
                    );
                    setNovelIdeas(novel);
                    setTotalExperiments(novel.length);
                    break;

                // This receives one run at a time
                case "EXPERIMENT_RESULT":
                    const newResult: ExperimentResult = data;
                    setAllRunResults((prevResults) => [...prevResults, newResult]);
                    addLog(
                        `Run ${newResult.run_number} finished for: ${newResult.idea_name}`,
                        "info",
                    );
                    break;

                case "ERROR":
                    addLog(data, "error");
                    setJobStatus("failed");
                    break;
            }
        },
        [addLog],
    );

    const handleError = useCallback(
        (error: string) => {
            toast({
                title: "WebSocket Error",
                description: error,
                variant: "destructive",
            });
            addLog(error, "error");
        },
        [toast, addLog],
    );

    const { isConnected } = useWebSocket(handleMessage, handleError);

    // --- Memoized Grouping Logic ---
    const groupedExperiments = useMemo(() => {
        const groups: Map<string, GroupedExperiment> = new Map();
        novelIdeas.forEach((idea) => {
            // Use 'Name' from your sample code
            const ideaKey = idea.Name || idea.id;
            groups.set(ideaKey, {
                idea: idea,
                runs: [],
            });
        });

        allRunResults.forEach((runResult) => {
            const group = groups.get(runResult.idea_name);
            if (group) {
                const newRuns = [
                    ...group.runs.filter(
                        (r) => r.run_number !== runResult.run_number,
                    ),
                    runResult,
                ];
                newRuns.sort((a, b) => a.run_number - b.run_number);
                group.runs = newRuns;
            }
        });
        return novelIdeas.map((idea) => groups.get(idea.Name || idea.id)!);
    }, [novelIdeas, allRunResults]);

    // For the main progress bar
    const ideasProcessed = useMemo(() => {
        return groupedExperiments.filter((g) => g.runs.length > 0).length;
    }, [groupedExperiments]);

    return (
        <div className="flex h-full">
            {/* Main Content Area (Chat UI) */}
            <div className="flex-1 p-6 overflow-y-auto">
                <h1 className="text-3xl font-bold mb-2">Experiment</h1>
                <p className="text-muted-foreground mb-6">
                    Job ID: <span className="font-mono">{jobId}</span>
                </p>

                {!isConnected && jobStatus !== "complete" && (
                    <div className="flex items-center justify-center p-12">
                        <Loader className="h-8 w-8 animate-spin mr-2" />
                        <span className="text-lg text-muted-foreground">
              {jobStatus === "failed" ? "Connection lost" : "Connecting to live feed..."}
            </span>
                    </div>
                )}

                <div className="flex flex-col gap-6 max-w-4xl mx-auto">
                    {/* 1. Main Progress Bar */}
                    <JobProgressBar
                        completed={ideasProcessed}
                        total={totalExperiments}
                    />

                    {/* 2. Experiment Results */}
                    <div className="flex flex-col gap-4">
                        {groupedExperiments.map((groupedExp) => (
                            <GroupedExperimentCard
                                key={groupedExp.idea.Name || groupedExp.idea.id}
                                groupedExp={groupedExp}
                                baseline={baselineScore}
                            />
                        ))}
                    </div>

                    {/* 3. Paper Bank */}
                    {papers && (
                        <div className="flex flex-col gap-4">
                            <h2 className="text-2xl font-semibold">
                                Found {papers.paper_bank.length} Relevant Papers
                            </h2>
                            {papers.paper_bank.map((paper) => (
                                <PaperCard key={paper.id} paper={paper} />
                            ))}
                        </div>
                    )}
                </div>
            </div>

            {/* Right Sidebar (Log Feed) */}
            <aside className="w-96 border-l h-full">
                <LogFeed logs={logFeed} />
            </aside>
        </div>
    );
}