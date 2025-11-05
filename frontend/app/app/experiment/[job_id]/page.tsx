// Location: frontend/app/app/experiment/[job_id]/page.tsx
"use client";

import { useState, useCallback, useMemo, useEffect } from "react";
import dynamic from "next/dynamic";
import { useParams } from "next/navigation";
import { useWebSocket } from "@/hooks/useWebSocket";
import {
    LogEntry,
    PaperBank,
    Idea,
    ExperimentResult,
    GroupedExperiment,
    Job, // Import the new Job type
    ArtifactFolder,
    ArtifactNode,
    ArtifactFile,
} from "@/lib/types";
import { useToast } from "@/hooks/use-toast";
import { LogFeed } from "@/components/LogFeed";
import { PaperCard } from "@/components/PaperCard";
import { JobProgressBar } from "@/components/JobProgressBar";
import { GroupedExperimentCard } from "@/components/GroupedExperimentCard";
import { Button } from "@/components/ui/button";
import { Loader, AlertTriangle, Code2, Download, ClipboardCopy } from "lucide-react";
import { api } from "@/lib/api"; // Import api
import { useAuth } from "@/hooks/useAuth"; // Import useAuth
import { FileTree } from "@/components/FileTree";
import { PanelGroup, Panel, PanelResizeHandle } from "react-resizable-panels";

type MonacoEditorComponent = typeof import("@monaco-editor/react").default;

const MonacoEditor = dynamic(
    () => import("@monaco-editor/react"),
    { ssr: false },
) as unknown as MonacoEditorComponent;

type ViewMode = "overview" | "preview";

const inferLanguageFromPath = (path: string | null): string => {
    if (!path) return "plaintext";
    if (path.endsWith(".py")) return "python";
    if (path.endsWith(".ts")) return "typescript";
    if (path.endsWith(".tsx")) return "typescript";
    if (path.endsWith(".js")) return "javascript";
    if (path.endsWith(".jsx")) return "javascript";
    if (path.endsWith(".json")) return "json";
    if (path.endsWith(".md")) return "markdown";
    if (path.endsWith(".sh")) return "shell";
    if (path.endsWith(".txt")) return "plaintext";
    return "plaintext";
};

const pickDefaultFile = (node: ArtifactNode | null): string | null => {
    if (!node) return null;

    let fallback: string | null = null;
    let preferred: string | null = null;

    const traverse = (current: ArtifactNode) => {
        if (preferred) {
            return;
        }

        if (current.type === "file") {
            if (!fallback) {
                fallback = current.path;
            }

            if (current.name === "experiment.py") {
                preferred = current.path;
            }
            return;
        }

        current.children?.forEach(traverse);
    };

    traverse(node);

    return preferred ?? fallback;
};

const collectExpansionKeys = (rootKey: string, targetFile: string | null): Set<string> => {
    const expansion = new Set<string>();
    expansion.add(rootKey);

    if (!targetFile) {
        return expansion;
    }

    const segments = targetFile.split("/").filter(Boolean);
    if (segments.length <= 1) {
        return expansion;
    }

    let current = "";
    for (let i = 0; i < segments.length - 1; i += 1) {
        current = current ? `${current}/${segments[i]}` : segments[i];
        expansion.add(current);
    }

    return expansion;
};

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
    const [viewMode, setViewMode] = useState<ViewMode>("overview");

    const [artifactLoading, setArtifactLoading] = useState(false);
    const [artifactError, setArtifactError] = useState<string | null>(null);
    const [artifactFolders, setArtifactFolders] = useState<ArtifactFolder[]>([]);
    const [selectedFolderPath, setSelectedFolderPath] = useState<string | null>(null);
    const [activeIdeaLabel, setActiveIdeaLabel] = useState<string | null>(null);
    const [artifactTree, setArtifactTree] = useState<ArtifactNode | null>(null);
    const [treeExpandedPaths, setTreeExpandedPaths] = useState<Set<string>>(new Set());
    const [treeLoading, setTreeLoading] = useState(false);
    const [selectedFilePath, setSelectedFilePath] = useState<string | null>(null);
    const [fileContent, setFileContent] = useState<string>("// Select a file to preview");
    const [fileLoading, setFileLoading] = useState(false);
    const [downloadLoading, setDownloadLoading] = useState(false);

    const loadFileContent = useCallback(
        (folderPath: string, filePathValue: string) => {
            if (!token || !jobId) {
                return;
            }

            setFileLoading(true);
            setSelectedFilePath(filePathValue);
            setArtifactError(null);

            api.get(`/jobs/${jobId}/artifacts/file?folder=${encodeURIComponent(folderPath)}&path=${encodeURIComponent(filePathValue)}`, token)
                .then((file: ArtifactFile) => {
                    setFileContent(file.content ?? "");
                })
                .catch((err) => {
                    console.error("Failed to load artifact file:", err);
                    setArtifactError(err.message || "Failed to load file contents.");
                    setFileContent("// Unable to load file");
                })
                .finally(() => {
                    setFileLoading(false);
                });
        },
        [jobId, token],
    );

    const toggleTreePath = useCallback((path: string) => {
        setTreeExpandedPaths((prev) => {
            const next = new Set(prev);
            if (next.has(path)) {
                next.delete(path);
            } else {
                next.add(path);
            }
            return next;
        });
    }, []);

    const handleSelectFile = useCallback(
        (path: string) => {
            if (!selectedFolderPath) {
                return;
            }

            if (path === selectedFilePath) {
                return;
            }

            loadFileContent(selectedFolderPath, path);
        },
        [loadFileContent, selectedFilePath, selectedFolderPath],
    );

    useEffect(() => {
        if (!selectedFolderPath) {
            setActiveIdeaLabel(null);
            return;
        }

        const matchingFolder = artifactFolders.find((folder) => folder.folder_path === selectedFolderPath);
        if (matchingFolder) {
            if (matchingFolder.is_root) {
                setActiveIdeaLabel("All artifacts");
            } else {
                setActiveIdeaLabel(matchingFolder.idea_title || matchingFolder.idea_name || matchingFolder.folder_name);
            }
        } else {
            setActiveIdeaLabel(selectedFolderPath);
        }
    }, [artifactFolders, selectedFolderPath]);

    useEffect(() => {
        if (jobStatus !== "complete" || !token || !jobId) {
            return;
        }

        setArtifactLoading(true);
        setArtifactError(null);

        api.get(`/jobs/${jobId}/artifacts/list`, token)
            .then((folders: ArtifactFolder[]) => {
                setArtifactFolders(folders);
                setSelectedFolderPath((prev) => {
                    if (prev && folders.some((folder) => folder.folder_path === prev)) {
                        return prev;
                    }
                    const rootFolder = folders.find((folder) => folder.is_root);
                    if (rootFolder) {
                        return rootFolder.folder_path;
                    }
                    return folders.length > 0 ? folders[0].folder_path : null;
                });
            })
            .catch((err) => {
                console.error("Failed to load job artifacts:", err);
                setArtifactError(err.message || "Unable to load code artifacts for this job.");
                setArtifactFolders([]);
                setSelectedFolderPath(null);
            })
            .finally(() => {
                setArtifactLoading(false);
            });
    }, [jobStatus, token, jobId]);

    useEffect(() => {
        if (viewMode !== "preview" || !selectedFolderPath || !token || !jobId) {
            return;
        }

        setTreeLoading(true);
        setArtifactError(null);
        setArtifactTree(null);

        api.get(`/jobs/${jobId}/artifacts/tree?folder=${encodeURIComponent(selectedFolderPath)}`, token)
            .then((tree: ArtifactNode) => {
                setArtifactTree(tree);
                const rootKey = tree.path && tree.path.length > 0 ? tree.path : (tree.name || "/");
                const defaultFile = pickDefaultFile(tree);
                const expansions = collectExpansionKeys(rootKey, defaultFile);
                setTreeExpandedPaths(expansions);

                if (defaultFile) {
                    loadFileContent(selectedFolderPath, defaultFile);
                } else {
                    setSelectedFilePath(null);
                    setFileContent("// Select a file to preview");
                }
            })
            .catch((err) => {
                console.error("Failed to load file tree:", err);
                setArtifactError(err.message || "Unable to load artifact tree.");
                setArtifactTree(null);
            })
            .finally(() => {
                setTreeLoading(false);
        });
    }, [viewMode, selectedFolderPath, token, jobId, loadFileContent]);

    useEffect(() => {
        if (jobStatus !== "complete" && viewMode === "preview") {
            setViewMode("overview");
        }
    }, [jobStatus, viewMode]);

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

    const previewDisabled = useMemo(() => jobStatus !== "complete", [jobStatus]);

    const handleDownloadFolder = useCallback(async () => {
        if (!selectedFolderPath || !token || !jobId) {
            toast({
                title: "Download unavailable",
                description: "Select a folder to download and ensure you are signed in.",
                variant: "destructive",
            });
            return;
        }

        try {
            setDownloadLoading(true);
            const blob = await api.download(`/jobs/${jobId}/artifacts/download?folder=${encodeURIComponent(selectedFolderPath)}`, token);
            const objectUrl = window.URL.createObjectURL(blob);
            const link = document.createElement("a");
            const folderSegments = selectedFolderPath.split("/").filter(Boolean);
            const lastSegment = folderSegments[folderSegments.length - 1] || "artifacts";
            link.href = objectUrl;
            link.download = `${lastSegment}.zip`;
            document.body.appendChild(link);
            link.click();
            link.remove();
            window.URL.revokeObjectURL(objectUrl);
        } catch (err: any) {
            console.error("Failed to download artifacts:", err);
            toast({
                title: "Download failed",
                description: err?.message || "Unable to download artifacts.",
                variant: "destructive",
            });
        } finally {
            setDownloadLoading(false);
        }
    }, [jobId, selectedFolderPath, token, toast]);

    const handleCopyFile = useCallback(async () => {
        if (!selectedFilePath || !fileContent || fileContent.startsWith("// Select a file")) {
            toast({
                title: "No file selected",
                description: "Choose a file in the tree before copying.",
            });
            return;
        }

        try {
            await navigator.clipboard.writeText(fileContent);
            toast({
                title: "Copied",
                description: `${selectedFilePath} copied to clipboard.`,
            });
        } catch (err) {
            console.error("Clipboard copy failed:", err);
            toast({
                title: "Copy failed",
                description: "Your browser blocked clipboard access.",
                variant: "destructive",
            });
        }
    }, [fileContent, selectedFilePath, toast]);

    // --- Render Logic ---
    if (pageLoading) {
        return (
            <div className="relative flex h-full w-full bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 text-white items-center justify-center p-12 overflow-hidden shadow-2xl">
                {/* Animated background gradient orbs */}
                <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-indigo-500/10 to-purple-600/10 rounded-full blur-3xl animate-pulse" />
                <div className="absolute bottom-0 left-0 w-40 h-40 bg-gradient-to-br from-cyan-500/10 to-blue-600/10 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />

                <div className="relative z-10 flex flex-col items-center justify-center gap-4">
                    <div className="bg-gradient-to-br from-indigo-500/20 to-purple-500/20 w-20 h-20 rounded-2xl flex items-center justify-center border border-indigo-400/30 shadow-lg">
                        <Loader className="h-10 w-10 text-indigo-300 animate-spin" />
                    </div>
                    <p className="text-lg text-white/70 font-semibold">Loading Experiment...</p>
                    <div className="flex gap-1.5 mt-2">
                        <div className="w-2 h-2 bg-indigo-400/50 rounded-full animate-pulse"></div>
                        <div className="w-2 h-2 bg-purple-400/50 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
                        <div className="w-2 h-2 bg-pink-400/50 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
                    </div>
                </div>
            </div>
        );
    }

    if (pageError) {
        return (
            <div className="relative flex h-full w-full bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 text-white flex-col items-center justify-center p-12 overflow-hidden shadow-2xl gap-4">
                {/* Animated background gradient orbs */}
                <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-indigo-500/10 to-purple-600/10 rounded-full blur-3xl animate-pulse" />
                <div className="absolute bottom-0 left-0 w-40 h-40 bg-gradient-to-br from-cyan-500/10 to-blue-600/10 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />

                <div className="relative z-10 flex flex-col items-center justify-center gap-4 text-red-400">
                    <div className="bg-gradient-to-br from-red-500/20 to-pink-500/20 w-20 h-20 rounded-2xl flex items-center justify-center border border-red-400/30 shadow-lg">
                        <AlertTriangle className="h-10 w-10" />
                    </div>
                    <h2 className="text-2xl font-bold bg-gradient-to-r from-red-400 via-pink-400 to-purple-400 bg-clip-text text-transparent">Error Loading Job</h2>
                    <p className="text-sm text-red-300/70">{pageError}</p>
                </div>
            </div>
        );
    }

    return (
        <div className="relative flex h-full w-full bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 text-white overflow-hidden shadow-2xl">
            {/* Animated background gradient orbs */}
            <div className="absolute top-0 right-0 w-40 h-40 bg-gradient-to-br from-indigo-500/20 to-purple-600/20 rounded-full blur-3xl animate-pulse" />
            <div className="absolute top-32 left-0 w-32 h-32 bg-gradient-to-br from-cyan-500/15 to-blue-600/15 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '0.5s' }} />
            <div className="absolute bottom-32 right-0 w-36 h-36 bg-gradient-to-br from-purple-500/15 to-pink-600/15 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
            <div className="absolute bottom-0 left-0 w-44 h-44 bg-gradient-to-br from-violet-500/20 to-fuchsia-600/20 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1.5s' }} />

            {/* Subtle gradient overlay for depth */}
            <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-indigo-950/10" />

            <div className={`relative z-10 flex-1 p-6 ${viewMode === "preview" ? "overflow-hidden" : "overflow-y-auto"}`}>
                <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
                    <div>
                        <h1 className="mb-2 text-3xl font-bold bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">Experiment</h1>
                        <p className="text-xs text-indigo-300/60 font-medium tracking-wide">
                            Job ID: <span className="font-mono">{jobId}</span>
                        </p>
                    </div>
                    <div className="flex items-center gap-3">
                        {shouldConnect && !isConnected && (
                            <span className="flex items-center gap-2 text-indigo-300/70 text-xs font-medium">
                                <Loader className="h-4 w-4 animate-spin text-indigo-400" />
                                Connecting...
                            </span>
                        )}
                        {shouldConnect && isConnected && (
                            <span className="flex items-center gap-2 text-green-400 text-xs font-medium">
                                <div className="h-3 w-3 rounded-full bg-green-400 animate-pulse" />
                                Live
                            </span>
                        )}
                        {jobStatus === "complete" && (
                            <span className="text-xs bg-gradient-to-r from-indigo-500/30 to-purple-500/30 text-indigo-200 px-2.5 py-1 rounded-full font-semibold border border-indigo-400/30">
                                Status: Complete
                            </span>
                        )}
                        {jobStatus === "complete" && (
                            <Button
                                variant="ghost"
                                className={
                                    viewMode === "preview"
                                        ? "bg-gradient-to-r from-indigo-500/90 to-purple-600/90 text-white shadow-lg shadow-indigo-500/50 hover:shadow-indigo-500/60 hover:from-indigo-500 hover:to-purple-600 scale-[1.02] border-indigo-400/50"
                                        : "bg-white/5 text-white/90 hover:bg-gradient-to-r hover:from-indigo-500/20 hover:to-purple-500/20 hover:text-white hover:scale-[1.02] border-white/10 hover:border-indigo-400/40"
                                }
                                disabled={previewDisabled && viewMode !== "preview"}
                                onClick={() => setViewMode(viewMode === "preview" ? "overview" : "preview")}
                            >
                                {viewMode === "preview" ? "Back to Overview" : "Preview Code"}
                            </Button>
                        )}
                    </div>
                </div>

                {viewMode === "overview" ? (
                    <div className="mx-auto flex max-w-4xl flex-col gap-6 pb-24 relative z-10">
                        <JobProgressBar completed={ideasProcessed} total={totalExperiments} />

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
                                <h2 className="text-2xl font-semibold bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
                                    Found {papers.paper_bank.length} Relevant Papers
                                </h2>
                                {papers.paper_bank.map((paper) => (
                                    <PaperCard key={paper.id} paper={paper} />
                                ))}
                            </div>
                        )}
                    </div>
                ) : (
                    <div className="flex h-full flex-col gap-4 relative z-10">
                        <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-indigo-500/20 bg-gradient-to-r from-gray-900/80 to-gray-900/60 backdrop-blur-sm px-4 py-3 shadow-sm">
                            <div>
                                <div className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wide bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
                                    <Code2 className="h-4 w-4" />
                                    Code Preview Mode
                                </div>
                                <p className="text-sm text-indigo-300/60">
                                    {activeIdeaLabel ? `Reviewing: ${activeIdeaLabel}` : "Select an experiment to inspect its generated code."}
                                </p>
                            </div>
                            <div className="flex items-center gap-2">
                                <Button
                                    variant="ghost"
                                    size="icon"
                                    className="bg-white/5 text-white/90 hover:bg-gradient-to-r hover:from-indigo-500/20 hover:to-purple-500/20 hover:text-white hover:scale-[1.02] border-white/10 hover:border-indigo-400/40"
                                    onClick={handleDownloadFolder}
                                    disabled={!selectedFolderPath || downloadLoading}
                                    aria-label="Download folder"
                                >
                                    {downloadLoading ? (
                                        <Loader className="h-4 w-4 animate-spin" />
                                    ) : (
                                        <Download className="h-4 w-4" />
                                    )}
                                </Button>
                                <Button
                                    variant="ghost"
                                    size="icon"
                                    className="bg-white/5 text-white/90 hover:bg-gradient-to-r hover:from-indigo-500/20 hover:to-purple-500/20 hover:text-white hover:scale-[1.02] border-white/10 hover:border-indigo-400/40"
                                    onClick={handleCopyFile}
                                    disabled={!selectedFilePath || fileLoading}
                                    aria-label="Copy file contents"
                                >
                                    <ClipboardCopy className="h-4 w-4" />
                                </Button>
                                <Button
                                    variant="ghost"
                                    className="bg-white/5 text-white/90 hover:bg-gradient-to-r hover:from-indigo-500/20 hover:to-purple-500/20 hover:text-white hover:scale-[1.02] border-white/10 hover:border-indigo-400/40"
                                    onClick={() => setViewMode("overview")}
                                >
                                    Return to Summary
                                </Button>
                            </div>
                        </div>

                        <div className="flex-1 overflow-hidden rounded-xl border border-indigo-500/20 bg-gradient-to-br from-gray-900/80 to-gray-900/60 backdrop-blur-sm shadow-inner">
                            {artifactLoading && !artifactTree ? (
                                <div className="flex h-full items-center justify-center gap-2 text-indigo-300/70">
                                    <Loader className="h-5 w-5 animate-spin text-indigo-400" /> Preparing artifacts...
                                </div>
                            ) : artifactFolders.length === 0 ? (
                                <div className="flex h-full items-center justify-center text-center text-sm text-indigo-300/60">
                                    No completed experiment artifacts are available yet.
                                </div>
                            ) : artifactError ? (
                                <div className="flex h-full flex-col items-center justify-center gap-2 text-center text-sm text-red-400">
                                    <AlertTriangle className="h-6 w-6" />
                                    {artifactError}
                                </div>
                            ) : treeLoading && !artifactTree ? (
                                <div className="flex h-full items-center justify-center gap-2 text-indigo-300/70">
                                    <Loader className="h-5 w-5 animate-spin text-indigo-400" /> Loading file tree...
                                </div>
                            ) : artifactTree ? (
                                <PanelGroup direction="horizontal" className="h-full">
                                    <Panel defaultSize={24} minSize={16} className="flex flex-col border-r border-indigo-500/30 bg-indigo-900/20 backdrop-blur-sm">
                                        <div className="border-b border-indigo-500/30 px-4 py-2 text-xs font-semibold uppercase tracking-wide text-indigo-300/80">
                                            Files
                                        </div>
                                        <div className="flex-1 overflow-auto p-2">
                                            <FileTree
                                                root={artifactTree}
                                                expandedPaths={treeExpandedPaths}
                                                onToggle={toggleTreePath}
                                                onSelectFile={handleSelectFile}
                                                selectedFile={selectedFilePath}
                                            />
                                        </div>
                                    </Panel>
                                    <PanelResizeHandle className="w-[1px] bg-indigo-500/30 transition hover:bg-indigo-400/70" />
                                    <Panel defaultSize={76} minSize={30} className="flex flex-col bg-[#0b1120]">
                                        <div className="border-b border-indigo-500/30 px-4 py-2 text-xs font-semibold uppercase tracking-wide text-indigo-300/80">
                                            {selectedFilePath || "Select a file"}
                                        </div>
                                        <div className="flex-1 overflow-hidden">
                                            {fileLoading ? (
                                                <div className="flex h-full items-center justify-center gap-2 text-indigo-300/80">
                                                    <Loader className="h-5 w-5 animate-spin text-indigo-400" /> Rendering source...
                                                </div>
                                            ) : (
                                                <MonacoEditor
                                                    language={inferLanguageFromPath(selectedFilePath)}
                                                    value={fileContent}
                                                    theme="vs-dark"
                                                    height="100%"
                                                    options={{
                                                        readOnly: true,
                                                        minimap: { enabled: false },
                                                        fontSize: 14,
                                                        smoothScrolling: true,
                                                        scrollBeyondLastLine: false,
                                                        automaticLayout: true,
                                                        renderLineHighlight: "all",
                                                    }}
                                                />
                                            )}
                                        </div>
                                    </Panel>
                                </PanelGroup>
                            ) : (
                                <div className="flex h-full items-center justify-center text-sm text-indigo-300/60">
                                    Select an experiment to explore its generated files.
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>
            {viewMode === "overview" && (
                <aside className="relative h-full w-96 border-l border-indigo-500/20 overflow-hidden shadow-2xl">
                    <LogFeed logs={logFeed} />
                </aside>
            )}
        </div>
    );
}