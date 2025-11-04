// Location: frontend/app/app/experiment/[job_id]/page.tsx
"use client";

import { useState, useCallback, useMemo, useEffect } from "react";
import { useParams } from "next/navigation";
import { useWebSocket } from "@/hooks/useWebSocket";
import {
    LogEntry,
    PaperBank,
    Idea,
    ExperimentResult,
    GroupedExperiment,
    Job, // Import the new Job type
} from "@/lib/types";
import { useToast } from "@/hooks/use-toast";
import { LogFeed } from "@/components/LogFeed";
import { PaperCard } from "@/components/PaperCard";
import { JobProgressBar } from "@/components/JobProgressBar";
import { GroupedExperimentCard } from "@/components/GroupedExperimentCard";
import { Loader, AlertTriangle } from "lucide-react";
import { api } from "@/lib/api"; // Import api
import { useAuth } from "@/hooks/useAuth"; // Import useAuth

export default function ExperimentPage() {
    const params = useParams();
    const { toast } = useToast();
    const { token } = useAuth(); // Get auth token
    const jobId = Array.isArray(params.job_id) ? params.job_id[0] : params.job_id;

    // --- Page State ---
    const [pageLoading, setPageLoading] = useState(true);
    const [pageError, setPageError] = useState<string | null>(null);

    // --- State Management ---
    const [logFeed, setLogFeed] = useState<LogEntry[]>([]);
    const [papers, setPapers] = useState<PaperBank | null>(null);
    const [baselineScore, setBaselineScore] = useState<number | null>(null);
    const [novelIdeas, setNovelIdeas] = useState<Idea[]>([]);
    const [totalExperiments, setTotalExperiments] = useState(0);
    const [allRunResults, setAllRunResults] = useState<ExperimentResult[]>([]);
    const [jobStatus, setJobStatus] = useState("loading");

    // Helper to add logs, ensuring most recent is at the top
    const addLog = useCallback(
        (message: string, log_type: LogEntry["log_type"] = "system") => {
            const newLog: LogEntry = {
                id: crypto.randomUUID(),
                message,
                log_type,
                timestamp: new Date().toLocaleTimeString(),
            };
            setLogFeed((prevLogs) => [newLog, ...prevLogs.slice(0, 200)]);
        },
        [],
    );

    // --- STAGE 4: Load Historical Data ---
    useEffect(() => {
        if (token && jobId) {
            setPageLoading(true);
            setPageError(null);

            api.get(`/jobs/${jobId}`, token)
                .then((job: Job) => {
                    // 1. Set Job Status
                    setJobStatus(job.status);

                    // 2. Set Papers & Baseline
                    if (job.papers) {
                        setPapers(job.papers);
                        const baseline = job.papers.baseline_score || 0.9105; // Use default
                        setBaselineScore(baseline);
                        addLog(`Loaded ${job.papers.paper_bank.length} papers.`, "system");
                        addLog(`Baseline score set to: ${baseline.toFixed(4)}`, "system");
                    }

                    // 3. Set Novel Ideas (the ones to be run)
                    if (job.ideas) {
                        setNovelIdeas(job.ideas);
                        setTotalExperiments(job.ideas.length);
                        addLog(`Loaded ${job.ideas.length} novel ideas.`, "system");
                    }

                    // 4. Set ALL past experiment results
                    if (job.experiment_results) {
                        setAllRunResults(job.experiment_results);
                        addLog(`Loaded ${job.experiment_results.length} past experiment runs.`, "system");
                    }

                    // 5. Load log history (if we stored it - for now, we just log)
                    if(job.status === 'complete' || job.status === 'failed') {
                        addLog(`Job is ${job.status}. No live updates.`, "system");
                    }

                })
                .catch((err) => {
                    console.error("Failed to load job history:", err);
                    setPageError(err.message || "Failed to load job.");
                    addLog(err.message || "Failed to load job.", "error");
                })
                .finally(() => {
                    setPageLoading(false);
                });
        }
    }, [jobId, token, addLog]); // Rerun if jobId or token changes

    // --- WebSocket Handlers (same as before) ---
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
                    if (!papers) { // Only set if not loaded from history
                        setPapers(data as PaperBank);
                        addLog("Research papers have been collected.", "info");
                        const baseline = data.baseline_score || 0.9105;
                        setBaselineScore(baseline);
                        addLog(`Baseline score set to: ${baseline.toFixed(4)}`, "system");
                    }
                    break;

                case "NOVEL_IDEAS_UPDATED":
                    if (novelIdeas.length === 0) { // Only set if not loaded
                        const novel: Idea[] = data;
                        addLog(
                            `Novelty check complete. ${novel.length} ideas will be run.`,
                            "success",
                        );
                        setNovelIdeas(novel);
                        setTotalExperiments(novel.length);
                    }
                    break;

                case "EXPERIMENT_RESULT":
                    const newResult: ExperimentResult = data;
                    // Add result, preventing duplicates
                    setAllRunResults((prevResults) => {
                        const exists = prevResults.some(
                            r => r.idea_name === newResult.idea_name && r.run_number === newResult.run_number
                        );
                        if (exists) return prevResults;
                        return [...prevResults, newResult];
                    });
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
        [addLog, papers, novelIdeas.length],
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

    // --- WebSocket Connection ---
    // Only connect if the page is done loading and the job is NOT finished.
    const shouldConnect =
        !pageLoading && jobStatus !== "complete" && jobStatus !== "failed";
    const { isConnected } = useWebSocket(
        handleMessage,
        handleError,
        shouldConnect, // Pass the connection condition to the hook
    );

    // --- Memoized Grouping Logic (same as before) ---
    const groupedExperiments = useMemo(() => {
        const groups: Map<string, GroupedExperiment> = new Map();
        novelIdeas.forEach((idea) => {
            const ideaKey = idea.Name || idea.id;
            groups.set(ideaKey, { idea: idea, runs: [] });
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

    const ideasProcessed = useMemo(() => {
        return groupedExperiments.filter((g) => g.runs.length > 0).length;
    }, [groupedExperiments]);

    // --- Render Logic ---
    if (pageLoading) {
        return (
            <div className="flex h-full items-center justify-center p-12">
                <Loader className="h-8 w-8 animate-spin mr-2" />
                <span className="text-lg text-muted-foreground">Loading Experiment...</span>
            </div>
        );
    }

    if (pageError) {
        return (
            <div className="flex h-full flex-col gap-4 items-center justify-center p-12 text-destructive">
                <AlertTriangle className="h-12 w-12" />
                <h2 className="text-2xl font-bold">Error Loading Job</h2>
                <p>{pageError}</p>
            </div>
        );
    }

    return (
        <div className="flex h-full">
            {/* Main Content Area (Chat UI) */}
            <div className="flex-1 p-6 overflow-y-auto">
                <div className="flex justify-between items-center">
                    <div>
                        <h1 className="text-3xl font-bold mb-2">Experiment</h1>
                        <p className="text-muted-foreground mb-6">
                            Job ID: <span className="font-mono">{jobId}</span>
                        </p>
                    </div>
                    <div className="flex items-center gap-2">
                        {shouldConnect && !isConnected && (
                            <span className="flex items-center gap-2 text-muted-foreground">
                <Loader className="h-4 w-4 animate-spin" />
                Connecting...
              </span>
                        )}
                        {shouldConnect && isConnected && (
                            <span className="flex items-center gap-2 text-green-500">
                <div className="h-3 w-3 rounded-full bg-green-500 animate-pulse" />
                Live
              </span>
                        )}
                        {jobStatus === 'complete' && (
                            <span className="font-medium p-2 px-3 bg-secondary rounded-md">
                Status: Complete
              </span>
                        )}
                    </div>
                </div>

                <div className="flex flex-col gap-6 max-w-4xl mx-auto">
                    <JobProgressBar
                        completed={ideasProcessed}
                        total={totalExperiments}
                    />

                    <div className="flex flex-col gap-4">
                        {groupedExperiments.map((groupedExp) => (
                            <GroupedExperimentCard
                                key={groupedExp.idea.Name || groupedExp.idea.id}
                                groupedExp={groupedExp}
                                baseline={baselineScore}
                            />
                        ))}
                    </div>

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