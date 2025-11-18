// Location: frontend/app/app/experiment/[job_id]/page.tsx
"use client";
import { useState, useCallback, useMemo, useEffect } from "react";
import dynamic from "next/dynamic";
import { useParams } from "next/navigation";
import { useWebSocket } from "@/hooks/useWebSocket";
import {
  LogEntry,
  PaperBank,
  Paper,
  PaperReview,
  Idea,
  ExperimentResult,
  GroupedExperiment,
  Job,
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
import { Loader, AlertTriangle, Code2, Download, ClipboardCopy, CheckCircle, XCircle, Edit3, Send, BookText } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";
import { FileTree } from "@/components/FileTree";
import { PanelGroup, Panel, PanelResizeHandle } from "react-resizable-panels";
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { ScrollArea } from "@/components/ui/scroll-area";

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
    if (preferred) return;
    if (current.type === "file") {
      if (!fallback) fallback = current.path;
      if (current.name === "experiment.py") preferred = current.path;
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
  if (!targetFile) return expansion;
  const segments = targetFile.split("/").filter(Boolean);
  if (segments.length <= 1) return expansion;
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
  const { token } = useAuth();
  const jobId = Array.isArray(params.job_id) ? params.job_id[0] : params.job_id;

  // --- Page State ---
  const [pageLoading, setPageLoading] = useState(true);
  const [pageError, setPageError] = useState<string | null>(null);

  // --- Core State ---
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
  const [paperReview, setPaperReview] = useState<PaperReview | null>(null);
  const [selectedPaperIds, setSelectedPaperIds] = useState<Set<string>>(new Set());
  const [paperComment, setPaperComment] = useState<string>("");
  const [paperSelectionSubmitting, setPaperSelectionSubmitting] = useState(false);

  // --- HITL State ---
  const [currentIdeaIdx, setCurrentIdeaIdx] = useState<number>(0);
  const [currentIdea, setCurrentIdea] = useState<Idea | null>(null);
  const [currentCode, setCurrentCode] = useState<string>("");
  const [feedbackLabel, setFeedbackLabel] = useState<"Promising" | "Needs Work" | "Reject">("Promising");
  const [feedbackComment, setFeedbackComment] = useState("");
  const [submittingFeedback, setSubmittingFeedback] = useState(false);

  const loadFileContent = useCallback(
    (folderPath: string, filePathValue: string) => {
      if (!token || !jobId) return;
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
      if (!selectedFolderPath || path === selectedFilePath) return;
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
    if (jobStatus !== "complete" || !token || !jobId) return;
    setArtifactLoading(true);
    setArtifactError(null);
    api.get(`/jobs/${jobId}/artifacts/list`, token)
      .then((folders: ArtifactFolder[]) => {
        setArtifactFolders(folders);
        setSelectedFolderPath((prev) => {
          if (prev && folders.some((folder) => folder.folder_path === prev)) return prev;
          const rootFolder = folders.find((folder) => folder.is_root);
          if (rootFolder) return rootFolder.folder_path;
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
    if (viewMode !== "preview" || !selectedFolderPath || !token || !jobId) return;
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

  const togglePaperSelection = useCallback((paperId: string, checked: boolean) => {
    setSelectedPaperIds((prev) => {
      const next = new Set(prev);
      if (checked) {
        next.add(paperId);
      } else {
        next.delete(paperId);
      }
      return next;
    });
  }, []);

  const selectedPaperIdsArray = useMemo(() => Array.from(selectedPaperIds), [selectedPaperIds]);

  const canSubmitPaperSelection = useMemo(() => {
    return selectedPaperIdsArray.length > 0 || paperComment.trim().length > 0;
  }, [selectedPaperIdsArray, paperComment]);

  const selectedPaperDetails = useMemo(() => {
    if (!papers) return [] as Paper[];
    return papers.paper_bank.filter((paper) => selectedPaperIds.has(paper.id));
  }, [papers, selectedPaperIds]);

  // --- NEW: Display only selected papers after review ---
  const displayedPapers = useMemo(() => {
    if (!papers) return [];
    // If paper review exists and not skipped, show only selected papers
    if (paperReview && !paperReview.skip && paperReview.selected_papers && paperReview.selected_papers.length > 0) {
      return paperReview.selected_papers;
    }
    // Otherwise show all papers
    return papers.paper_bank;
  }, [papers, paperReview]);
  // --- END NEW ---

  const submitPaperSelection = useCallback(async () => {
    if (!token || !jobId) {
      toast({ title: "Not authenticated", description: "Sign in to submit feedback.", variant: "destructive" });
      return;
    }
    if (!papers) {
      toast({ title: "Papers unavailable", description: "No papers to review right now.", variant: "destructive" });
      return;
    }
    if (!canSubmitPaperSelection) {
      toast({ title: "Nothing to submit", description: "Select at least one paper or add a comment.", variant: "destructive" });
      return;
    }

    const payload = {
      selected_paper_ids: selectedPaperIdsArray,
      comment: paperComment.trim() || undefined,
      skip: false,
    };

    const reviewSnapshot: PaperReview = {
      selected_paper_ids: selectedPaperIdsArray,
      selected_papers: selectedPaperDetails,
      comment: paperComment.trim() || null,
      skip: false,
      submitted_at: new Date().toISOString(),
    };

    setPaperSelectionSubmitting(true);
    try {
      await api.post(`/jobs/${jobId}/paper-review`, payload, token);
      setPaperReview(reviewSnapshot);
      setJobStatus("papers_reviewed");
      addLog(`Submitted paper feedback on ${selectedPaperIdsArray.length} papers.`, "info");
      setSelectedPaperIds(new Set());
      setPaperComment("");
    } catch (err: any) {
      const message = err instanceof ApiError ? err.message : "Failed to submit paper feedback.";
      toast({ title: "Submission failed", description: message, variant: "destructive" });
    } finally {
      setPaperSelectionSubmitting(false);
    }
  }, [token, jobId, papers, canSubmitPaperSelection, selectedPaperIdsArray, paperComment, selectedPaperDetails, addLog, toast]);

  const skipPaperSelection = useCallback(async () => {
    if (!token || !jobId) {
      toast({ title: "Not authenticated", description: "Sign in to continue.", variant: "destructive" });
      return;
    }

    const payload = {
      skip: true,
      comment: paperComment.trim() || undefined,
    };

    const reviewSnapshot: PaperReview = {
      selected_paper_ids: [],
      selected_papers: [],
      comment: paperComment.trim() || null,
      skip: true,
      submitted_at: new Date().toISOString(),
    };

    setPaperSelectionSubmitting(true);
    try {
      await api.post(`/jobs/${jobId}/paper-review`, payload, token);
      setPaperReview(reviewSnapshot);
      setJobStatus("papers_reviewed");
      addLog("Skipped paper review stage.", "info");
      setSelectedPaperIds(new Set());
      setPaperComment("");
    } catch (err: any) {
      const message = err instanceof ApiError ? err.message : "Failed to skip paper review.";
      toast({ title: "Skip failed", description: message, variant: "destructive" });
    } finally {
      setPaperSelectionSubmitting(false);
    }
  }, [token, jobId, paperComment, addLog, toast]);

  // --- Load Historical Data ---
  useEffect(() => {
    if (token && jobId) {
      setPageLoading(true);
      setPageError(null);
      api.get(`/jobs/${jobId}`, token)
        .then((job: Job) => {
          setJobStatus(job.status);
          setCurrentIdeaIdx(job.current_idea_idx || 0);
          if (job.paper_review) {
            setPaperReview(job.paper_review);
          }
          if (job.papers) {
            setPapers(job.papers);
            const baseline = job.papers.baseline_score || 0.9105;
            setBaselineScore(baseline);
            addLog(`Loaded ${job.papers.paper_bank.length} papers.`, "system");
            addLog(`Baseline score set to: ${baseline.toFixed(4)}`, "system");
          }
          if (job.ideas) {
            setNovelIdeas(job.ideas);
            setTotalExperiments(job.ideas.length);
            addLog(`Loaded ${job.ideas.length} novel ideas.`, "system");
          }
          if (job.experiment_results) {
            setAllRunResults(job.experiment_results);
            addLog(`Loaded ${job.experiment_results.length} past experiment runs.`, "system");
          }
          if (job.status === 'complete' || job.status === 'failed') {
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
  }, [jobId, token, addLog]);

  useEffect(() => {
    if (jobStatus === "pending_human_papers") {
      setSelectedPaperIds(new Set());
      setPaperComment("");
    }
  }, [jobStatus]);

  // --- WebSocket Handlers ---
  const handleMessage = useCallback(
    (message: any) => {
      const { type, data } = message;
      switch (type) {
        case "JOB_STATUS_UPDATE":
          setJobStatus(data.status);
          if (data.paper_review) {
            setPaperReview(data.paper_review as PaperReview);
          }
          if (data.status === "pending_human_papers") {
            setSelectedPaperIds(new Set());
            setPaperComment("");
          }
          if (data.current_idea_idx !== undefined) setCurrentIdeaIdx(data.current_idea_idx);
          if (data.status === "pending_human_idea" && data.idea) {
            setCurrentIdea(data.idea);
            addLog(`Idea #${data.current_idea_idx + 1} ready for approval.`, "info");
          }
          if (data.status === "pending_human_code" && data.code) {
            setCurrentCode(data.code);
            addLog("Code generated. Awaiting approval.", "info");
          }
          if (data.status === "complete" || data.status === "failed") {
            addLog(`Job ${data.status}.`, "success");
          }
          break;
        case "AIDER_LOG":
          addLog(data.message, data.log_type);
          break;
        case "PAPERS_UPDATED":
          if (!papers) {
            setPapers(data as PaperBank);
            addLog("Research papers have been collected.", "info");
            const baseline = data.baseline_score || 0.9105;
            setBaselineScore(baseline);
            addLog(`Baseline score set to: ${baseline.toFixed(4)}`, "system");
          }
          break;
        case "NOVEL_IDEAS_UPDATED":
          if (novelIdeas.length === 0) {
            const novel: Idea[] = data;
            addLog(`Novelty check complete. ${novel.length} ideas will be run.`, "success");
            setNovelIdeas(novel);
            setTotalExperiments(novel.length);
          }
          break;
        case "EXPERIMENT_RESULT":
          const newResult: ExperimentResult = data;
          setAllRunResults((prevResults) => {
            const exists = prevResults.some(
              r => r.idea_name === newResult.idea_name && r.run_number === newResult.run_number
            );
            if (exists) return prevResults;
            return [...prevResults, newResult];
          });
          addLog(`Run ${newResult.run_number} finished for: ${newResult.idea_name}`, "info");
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

  const shouldConnect = !pageLoading && jobStatus !== "complete" && jobStatus !== "failed";
  const { isConnected } = useWebSocket(handleMessage, handleError, shouldConnect, jobId);

  // --- Grouping Logic ---
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
          ...group.runs.filter((r) => r.run_number !== runResult.run_number),
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

  // --- HITL Actions ---
  const approveIdea = async () => {
    if (!token || !jobId) {
      toast({ title: "Not authenticated", description: "Please sign in before approving ideas.", variant: "destructive" });
      return;
    }
    try {
      await api.post(`/jobs/${jobId}/approve-idea`, {}, token);
      addLog("Idea approved. Generating code...");
    } catch (err: any) {
      toast({ title: "Error", description: err.message, variant: "destructive" });
    }
  };

  const approveCode = async () => {
    if (!token || !jobId) {
      toast({ title: "Not authenticated", description: "Please sign in before approving code.", variant: "destructive" });
      return;
    }
    try {
      await api.post(`/jobs/${jobId}/approve-code`, {}, token);
      addLog("Code approved. Running experiment...");
    } catch (err: any) {
      toast({ title: "Error", description: err.message, variant: "destructive" });
    }
  };

  const submitFeedback = async () => {
    if (!feedbackComment.trim()) {
      toast({ title: "Comment required", description: "Please add a comment.", variant: "destructive" });
      return;
    }
    setSubmittingFeedback(true);
    try {
      if (!token || !jobId) {
        toast({ title: "Not authenticated", description: "Please sign in before submitting feedback.", variant: "destructive" });
        return;
      }
      await api.post(
        `/jobs/${jobId}/submit-feedback`,
        { result: { label: feedbackLabel, comment: feedbackComment } },
        token
      );
      addLog(`Feedback sent: ${feedbackLabel}`);
      setFeedbackComment("");
    } catch (err: any) {
      toast({ title: "Error", description: err.message, variant: "destructive" });
    } finally {
      setSubmittingFeedback(false);
    }
  };

  // --- Render Logic ---
  if (pageLoading) {
    return (
      <div className="relative flex h-full w-full bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 text-white items-center justify-center p-12 overflow-hidden shadow-2xl">
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
      <div className="absolute top-0 right-0 w-40 h-40 bg-gradient-to-br from-indigo-500/20 to-purple-600/20 rounded-full blur-3xl animate-pulse" />
      <div className="absolute top-32 left-0 w-32 h-32 bg-gradient-to-br from-cyan-500/15 to-blue-600/15 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '0.5s' }} />
      <div className="absolute bottom-32 right-0 w-36 h-36 bg-gradient-to-br from-purple-500/15 to-pink-600/15 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
      <div className="absolute bottom-0 left-0 w-44 h-44 bg-gradient-to-br from-violet-500/20 to-fuchsia-600/20 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1.5s' }} />
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-indigo-950/10" />

      {jobStatus === "pending_human_papers" && papers && (
        <div className="fixed inset-0 z-50 flex items-center justify-center px-4 sm:px-8 py-6 bg-black/70 backdrop-blur-xl">
          <Card className="w-full max-w-5xl border-indigo-500/30 bg-gradient-to-br from-gray-900/95 to-gray-800/95 shadow-2xl">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-indigo-300">
                <BookText className="h-5 w-5" /> Review Retrieved Papers
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-5">
              <div className="rounded-lg border border-amber-500/30 bg-amber-900/10 px-4 py-3">
                <p className="text-sm text-amber-200/90">
                  <span className="font-semibold">💡 Important:</span> Only your selected papers will be used for idea generation. 
                  Choose papers that best align with your research direction.
                </p>
              </div>
              <p className="text-sm text-indigo-200/80">
                Select the papers that look most promising and add optional guidance to steer the next idea generation round.
              </p>
              <ScrollArea className="h-[45vh] rounded-lg border border-indigo-500/20 bg-indigo-900/10">
                {papers.paper_bank.length > 0 ? (
                  <div className="space-y-3 p-4 pr-6">
                    {papers.paper_bank.map((paper) => {
                      const checked = selectedPaperIds.has(paper.id);
                      return (
                        <label
                          key={paper.id}
                          className="flex items-start gap-3 rounded-lg border border-indigo-500/10 bg-gray-900/50 px-3 py-2 transition hover:border-indigo-400/40"
                        >
                          <Checkbox
                            checked={checked}
                            onCheckedChange={(value: boolean | "indeterminate") => togglePaperSelection(paper.id, value === true)}
                            className="mt-1"
                          />
                          <div className="space-y-1">
                            <p className="font-semibold text-white">{paper.title}</p>
                            <p className="text-xs text-indigo-200/70">
                              Year: {paper.year ?? "N/A"} · Score: {typeof paper.score === "number" ? paper.score.toFixed(2) : "N/A"}
                            </p>
                            <p className="text-xs text-gray-300 line-clamp-3">{paper.tldr || paper.abstract || "Summary unavailable."}</p>
                          </div>
                        </label>
                      );
                    })}
                  </div>
                ) : (
                  <div className="p-4 text-sm text-indigo-200/60">No papers were returned for this job.</div>
                )}
              </ScrollArea>
              <div>
                <Label htmlFor="paper-comment">Comment (optional)</Label>
                <Textarea
                  id="paper-comment"
                  value={paperComment}
                  onChange={(e) => setPaperComment(e.target.value)}
                  placeholder="Share insights, constraints, or ideas inspired by these papers..."
                  className="mt-2 bg-gray-800/80 border-gray-700 text-white"
                  rows={3}
                />
              </div>
            </CardContent>
            <CardFooter className="flex flex-wrap items-center justify-between gap-3">
              <span className="text-xs text-indigo-200/70">
                {selectedPaperIdsArray.length} paper{selectedPaperIdsArray.length === 1 ? "" : "s"} selected
              </span>
              <div className="flex gap-2">
                <Button variant="outline" onClick={skipPaperSelection} disabled={paperSelectionSubmitting}>
                  Skip for now
                </Button>
                <Button
                  onClick={submitPaperSelection}
                  disabled={paperSelectionSubmitting || !canSubmitPaperSelection}
                  className="bg-indigo-600 hover:bg-indigo-700"
                >
                  {paperSelectionSubmitting ? (
                    <span className="flex items-center gap-2">
                      <Loader className="h-4 w-4 animate-spin" />
                      Sending...
                    </span>
                  ) : (
                    <span>Use Selected Papers</span>
                  )}
                </Button>
              </div>
            </CardFooter>
          </Card>
        </div>
      )}

      {/* HITL: Idea Approval */}
      {jobStatus === "pending_human_idea" && (
        <div className="fixed inset-0 z-50 flex items-center justify-center px-4 sm:px-8 py-6 bg-black/70 backdrop-blur-xl">
          <Card className="w-full max-w-3xl border-indigo-500/30 bg-gradient-to-br from-gray-900/95 to-gray-800/95 shadow-2xl">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-indigo-300">
                <Edit3 className="h-5 w-5" /> Ideas Generated - Ready for Experiments
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {currentIdea ? (
                <div>
                  <h3 className="font-semibold text-white">{currentIdea.Title}</h3>
                  <p className="mt-1 text-sm text-gray-300">{currentIdea.Summary}</p>
                </div>
              ) : novelIdeas.length > 0 ? (
                <div className="space-y-3">
                  <p className="text-sm text-gray-300">
                    {novelIdeas.length} novel {novelIdeas.length === 1 ? 'idea has' : 'ideas have'} been generated and are ready for experimentation.
                  </p>
                  <div className="max-h-60 space-y-2 overflow-auto rounded-lg bg-gray-800/50 p-3">
                    {novelIdeas.map((idea, idx) => (
                      <div key={idx} className="rounded border border-indigo-500/20 bg-gray-900/50 p-2">
                        <p className="text-sm font-semibold text-white">{idx + 1}. {idea.Title || idea.Name}</p>
                        {idea.Summary && <p className="mt-1 text-xs text-gray-400 line-clamp-2">{idea.Summary}</p>}
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <p className="text-sm text-gray-300">Ideas are ready. Click below to start experiments.</p>
              )}
              <div className="flex flex-wrap gap-2">
                <Button onClick={approveIdea} className="bg-green-600 hover:bg-green-700">
                  <CheckCircle className="h-4 w-4 mr-1" /> Start Experiments
                </Button>
                <Button variant="outline" onClick={() => setJobStatus("pending_human_feedback")}>
                  <XCircle className="h-4 w-4 mr-1" /> Give Feedback First
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* HITL: Code Approval */}
      {jobStatus === "pending_human_code" && currentCode && (
        <div className="fixed inset-0 z-50 flex items-center justify-center px-4 sm:px-8 py-6 bg-black/70 backdrop-blur-xl">
          <Card className="w-full max-w-4xl border-indigo-500/30 bg-gradient-to-br from-gray-900/95 to-gray-800/95 shadow-2xl">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-indigo-300">
                <Code2 className="h-5 w-5" /> Review Generated Code
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="mb-4 h-[50vh] overflow-auto rounded-lg bg-gray-900/80 p-4 font-mono text-xs text-gray-300">
                <pre>{currentCode}</pre>
              </div>
              <div className="flex flex-wrap gap-2">
                <Button onClick={approveCode} className="bg-green-600 hover:bg-green-700">
                  <CheckCircle className="h-4 w-4 mr-1" /> Approve & Run
                </Button>
                <Button variant="outline" onClick={() => setJobStatus("pending_human_feedback")}>
                  <Edit3 className="h-4 w-4 mr-1" /> Edit & Resubmit
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* HITL: Feedback */}
      {jobStatus === "pending_human_feedback" && (
        <div className="fixed inset-0 z-50 flex items-center justify-center px-4 sm:px-8 py-6 bg-black/70 backdrop-blur-xl">
          <Card className="w-full max-w-3xl border-indigo-500/30 bg-gradient-to-br from-gray-900/95 to-gray-800/95 shadow-2xl">
            <CardHeader>
              <CardTitle className="text-indigo-300">Submit Feedback</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label>Assessment</Label>
                <div className="mt-2 flex flex-wrap gap-2">
                  {(["Promising", "Needs Work", "Reject"] as const).map((label) => (
                    <Button
                      key={label}
                      variant={feedbackLabel === label ? "default" : "outline"}
                      size="sm"
                      onClick={() => setFeedbackLabel(label)}
                    >
                      {label}
                    </Button>
                  ))}
                </div>
              </div>
              <div>
                <Label>Comment</Label>
                <Textarea
                  value={feedbackComment}
                  onChange={(e) => setFeedbackComment(e.target.value)}
                  placeholder="Suggest improvements, fixes, or next steps..."
                  className="mt-2 bg-gray-800/80 border-gray-700 text-white"
                  rows={3}
                />
              </div>
              <Button onClick={submitFeedback} disabled={submittingFeedback} className="bg-indigo-600 hover:bg-indigo-700">
                {submittingFeedback ? <Loader className="h-4 w-4 mr-2 animate-spin" /> : <Send className="h-4 w-4 mr-2" />}
                Submit Feedback
              </Button>
            </CardContent>
          </Card>
        </div>
      )}

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
                  {paperReview && !paperReview.skip && paperReview.selected_papers && paperReview.selected_papers.length > 0
                    ? `${displayedPapers.length} Selected Paper${displayedPapers.length === 1 ? '' : 's'}`
                    : `Found ${papers.paper_bank.length} Relevant Papers`}
                </h2>
                {paperReview && !paperReview.skip && paperReview.selected_papers && paperReview.selected_papers.length > 0 && (
                  <div className="mb-2 rounded-lg border border-indigo-500/30 bg-indigo-900/20 px-4 py-3">
                    <p className="text-sm text-indigo-200/90">
                      <span className="font-semibold">✓ Human Review Completed:</span> Showing only your selected papers
                      {paperReview.comment && (
                        <span className="block mt-1 text-indigo-300/70 italic">
                          "{paperReview.comment}"
                        </span>
                      )}
                    </p>
                  </div>
                )}
                {displayedPapers.map((paper) => (
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