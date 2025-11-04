import React, { useState, useEffect, useRef } from 'react';

// --- CONSTANTS ---
const MAX_RUNS = 5; // From experiments_utils.py

// --- INTERFACES ---

interface Job {
  _id: string;
  user_id: string;
  created_at: string;
  status: string;
  request: {
    topic: string;
    experiment: string;
  };
  papers: object | null;
  ideas: Idea[];
  experiment_results: ExperimentResult[]; // This will be the raw list
  log: string | null;
  error_log: string | null;
}

interface Idea {
  Name: string;
  Title: string;
  Summary: string;
  [key: string]: any;
}

// This now includes the run_number from the backend
interface ExperimentResult {
  idea_name: string;
  idea_title: string;
  run_number: number; // e.g., 1, 2, 3, 4, 5, or 99 for "final"
  metrics: any;
  folder_name: string;
}

interface LogEntry {
  timestamp: string;
  message: string;
  log_type: "info" | "success" | "fail" | "error" | "system";
}

interface WebSocketMessage {
  type: "JOB_UPDATE" | "JOB_STARTED" | "ERROR" | "JOB_STATUS_UPDATE"
      | "PAPERS_UPDATED" | "IDEAS_UPDATED"
      | "NOVEL_IDEAS_UPDATED" // <-- NEW: For the progress bar
      | "EXPERIMENT_RESULT"   // <-- This is a single RUN result
      | "AIDER_LOG";
  data: any;
}

// This is our new "grouped" data structure for rendering
interface GroupedExperiment {
  idea: Idea;
  runs: ExperimentResult[];
}

// --- HELPER FUNCTIONS & COMPONENTS ---

const PrettyJson: React.FC<{ data: any }> = ({ data }) => (
  <pre className="json-pre">
    {JSON.stringify(data, null, 2)}
  </pre>
);

const getMetric = (result: ExperimentResult): number | null => {
  try {
    const acc = result.metrics.sentiment.means.best_acc;
    return parseFloat(acc);
  } catch (e) {
    return null;
  }
};

const LogFeed: React.FC<{ logs: LogEntry[] }> = ({ logs }) => (
  <div className="log-feed">
    {logs.length === 0 && (
      <div className="log-entry log-type-system">Waiting for logs...</div>
    )}
    {logs.map((log, index) => (
      <div key={index} className={`log-entry log-type-${log.log_type}`}>
        <span className="log-timestamp">{log.timestamp}</span>
        <span className="log-message">{log.message}</span>
      </div>
    ))}
  </div>
);

// ---
// --- NEW: Component for the main progress bar
// ---
const JobProgressBar: React.FC<{
  completed: number,
  total: number
}> = ({ completed, total }) => {
  const percent = total > 0 ? (completed / total) * 100 : 0;

  return (
    <div className="progress-section">
      <div className="progress-header">
        <h3>Overall Experiment Progress</h3>
        <span>{completed} / {total} Ideas Processed</span>
      </div>
      <div className="progress-bar-container">
        <div
          className="progress-bar-inner"
          style={{ width: `${percent}%` }}
        >
          {percent > 10 && `${percent.toFixed(0)}%`}
        </div>
      </div>
    </div>
  );
};

// ---
// --- NEW: Component to show one Idea and its Runs
// ---
const GroupedExperimentCard: React.FC<{
  groupedExp: GroupedExperiment;
  baseline: number | null;
}> = ({ groupedExp, baseline }) => {
  const { idea, runs } = groupedExp;

  // Find the best run *within this group*
  const bestRun = runs
    .filter(r => r.run_number !== 99) // Exclude the "final" metric
    .sort((a, b) => (getMetric(b) ?? -1) - (getMetric(a) ?? -1))[0];

  const bestMetric = bestRun ? getMetric(bestRun) : null;

  let comparison = null;
  let metricClass = "metric-neutral";

  if (bestMetric !== null && baseline !== null) {
    const diff = bestMetric - baseline;
    if (diff > 0.0001) {
      comparison = `+${diff.toFixed(4)} vs Baseline`;
      metricClass = "metric-better";
    } else if (diff < -0.0001) {
      comparison = `${diff.toFixed(4)} vs Baseline`;
      metricClass = "metric-worse";
    } else {
      comparison = "Matches Baseline";
    }
  }

  // Mini progress bar for the runs
  const runsCompleted = runs.filter(r => r.run_number !== 99).length;
  const runPercent = (runsCompleted / MAX_RUNS) * 100;

  return (
    <div className={`grouped-card ${bestMetric && bestMetric > (baseline ?? 0) ? 'is-best' : ''}`}>
      {bestMetric && bestMetric > (baseline ?? 0) && <div className="best-badge">Best So Far</div>}
      <div className="grouped-card-header">
        <div>
          <h5 title={idea.Name}>{idea.Title}</h5>
          <p>{idea.Summary}</p>
        </div>
        {bestMetric !== null && (
          <div className={`metric-score ${metricClass}`}>
            {bestMetric.toFixed(4)}
            <span className="metric-label">Best Run (Acc)</span>
            <span className={`metric-comparison ${metricClass}`}>{comparison}</span>
          </div>
        )}
      </div>

      <div className="grouped-card-body">
        <h6>Aider Runs (Up to {MAX_RUNS})</h6>
        <div className="progress-bar-container mini-bar">
          <div
            className="progress-bar-inner"
            style={{ width: `${runPercent}%` }}
          />
        </div>
        <ul className="run-list">
          {runs.filter(r => r.run_number !== 99).map(run => (
            <li key={run.run_number} className={run === bestRun ? 'best-run' : ''}>
              <span>Run {run.run_number}</span>
              <span className="run-metric">{getMetric(run)?.toFixed(4) ?? 'N/A'}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};

// ---
// --- MAIN PAGE COMPONENT (MODIFIED) ---
// ---
export function LiveTestPage() {
  const [status, setStatus] = useState("Connecting to server...");
  const [isConnecting, setIsConnecting] = useState(true);
  const [isJobRunning, setIsJobRunning] = useState(false);

  const [logFeed, setLogFeed] = useState<LogEntry[]>([]);
  const [papers, setPapers] = useState<object | null>(null);
  const [baselineScore, setBaselineScore] = useState<number | null>(null);

  // --- NEW STATE MANAGEMENT ---
  // The list of ideas that will *actually* be run (after novelty check)
  const [novelIdeas, setNovelIdeas] = useState<Idea[]>([]);
  // The total number of experiments to run (from novelIdeas.length)
  const [totalExperiments, setTotalExperiments] = useState(0);
  // A raw list of all *run* results as they come in
  const [allRunResults, setAllRunResults] = useState<ExperimentResult[]>([]);
  // ---

  const socket = useRef<WebSocket | null>(null);

  const addLog = (message: string, log_type: LogEntry["log_type"] = "system") => {
    const newLog: LogEntry = {
      message,
      log_type,
      timestamp: new Date().toLocaleTimeString()
    };
    setLogFeed(prevLogs => [newLog, ...prevLogs.slice(0, 100)]);
  };

  const resetJobState = () => {
    setLogFeed([]);
    setPapers(null);
    setBaselineScore(null);
    setNovelIdeas([]);
    setTotalExperiments(0);
    setAllRunResults([]);
  };

  useEffect(() => {
    console.log("Connecting to WebSocket...");
    socket.current = new WebSocket("ws://localhost:8000/api/v1/ws");

    socket.current.onopen = () => {
      console.log("WebSocket connected!");
      setStatus("Connected. Ready to start a job.");
      setIsConnecting(false);
      addLog("WebSocket connected!", "success");
    };

    socket.current.onmessage = (event) => {
      const message: WebSocketMessage = JSON.parse(event.data);
      console.log("Received message:", message);

      switch (message.type) {

        case "JOB_STARTED":
          resetJobState();
          setStatus(`Job ${message.data.job_id} has started!`);
          setIsJobRunning(true);
          addLog(`Job ${message.data.job_id} started.`, "info");
          break;

        case "JOB_STATUS_UPDATE":
          setStatus(`Job status: ${message.data.status}`);
          if (message.data.status === 'complete' || message.data.status === 'failed') {
            setIsJobRunning(false);
            addLog("Job finished.", "success");
          }
          break;

        case "PAPERS_UPDATED":
          setPapers(message.data);
          addLog("Research papers have been collected.", "info");
          break;

        case "IDEAS_UPDATED":
          // This is the *initial* list. We just log it.
          addLog(`Generated ${message.data.length} initial ideas.`, "info");
          // SETTING BASELINE from your sample file
          const baseline = 0.9105504587155964;
          setBaselineScore(baseline);
          addLog(`Baseline score set to: ${baseline}`, "system");
          break;

        // --- THIS IS THE NEW KEY MESSAGE ---
        case "NOVEL_IDEAS_UPDATED":
          const novelIdeas: Idea[] = message.data;
          addLog(`Novelty check complete. ${novelIdeas.length} ideas will be run.`, "success");
          setNovelIdeas(novelIdeas);
          setTotalExperiments(novelIdeas.length);
          break;

        // --- THIS RECEIVES ONE RUN AT A TIME ---
        case "EXPERIMENT_RESULT":
          const newResult: ExperimentResult = message.data;
          setAllRunResults(prevResults => [...prevResults, newResult]);
          addLog(`Run ${newResult.run_number} finished for: ${newResult.idea_name}`, "info");
          break;

        case "AIDER_LOG":
          const logData = message.data as { message: string, log_type: LogEntry["log_type"] };
          addLog(logData.message, logData.log_type);
          setStatus(logData.message);
          break;

        case "ERROR":
          setStatus(`Error: ${message.data}`);
          setIsJobRunning(false);
          addLog(message.data, "error");
          break;
      }
    };

    socket.current.onclose = () => {
      console.log("WebSocket disconnected.");
      setStatus("Disconnected. Please refresh the page.");
      setIsConnecting(false);
      setIsJobRunning(false);
      addLog("WebSocket disconnected. Please refresh.", "error");
    };

    socket.current.onerror = (err) => {
      console.error("WebSocket error:", err);
      setStatus("Connection error. Is the backend server running?");
      setIsConnecting(false);
      addLog("Connection error. Is the backend server running?", "error");
    };

    return () => {
      if (socket.current) {
        socket.current.close();
      }
    };
  }, []);

  const startJob = () => {
    if (socket.current && socket.current.readyState === WebSocket.OPEN) {
      const researchRequest = {
        topic: "novel attention mechanisms for sentiment classification",
        experiment: "sentiment_classification_sst2",
        model: "gemini-2.5-flash-lite",
        code_model: "flash",
        num_ideas: 3, // Start with 3 ideas
        rag: true,
        check_similarity: true,
        skip_novelty_check: true, // <-- Let's run the novelty check
        round: 0,
        save_name: "letstestfinal"
      };

      const message = {
        type: "START_JOB",
        payload: researchRequest,
      };

      console.log("Sending START_JOB message...");
      socket.current.send(JSON.stringify(message));

      resetJobState();
      setStatus("Job start message sent...");
      setIsJobRunning(true);
      addLog("Sending START_JOB message...", "system");

    } else {
      setStatus("Not connected. Cannot start job.");
      addLog("Not connected. Cannot start job.", "error");
    }
  };

  // --- NEW: Memoized grouping logic ---
  const groupedExperiments = React.useMemo(() => {
    // 1. Create a map from the novelIdeas list
    const groups: Map<string, GroupedExperiment> = new Map();
    novelIdeas.forEach(idea => {
      groups.set(idea.Name, {
        idea: idea,
        runs: []
      });
    });

    // 2. Populate the runs from the raw results
    allRunResults.forEach(runResult => {
      const group = groups.get(runResult.idea_name);
      if (group) {
        // Add or update the result for this run number
        const newRuns = [...group.runs.filter(r => r.run_number !== runResult.run_number), runResult];
        newRuns.sort((a, b) => a.run_number - b.run_number); // Sort by run number
        group.runs = newRuns;
      }
    });

    // 3. Return an array in the order of novelIdeas
    return novelIdeas.map(idea => groups.get(idea.Name)!);

  }, [novelIdeas, allRunResults]);

  // For the main progress bar: count how many ideas have at least one run
  const ideasProcessed = React.useMemo(() => {
    return groupedExperiments.filter(g => g.runs.length > 0).length;
  }, [groupedExperiments]);


  return (
    <div className="container">
      <div className="card">
        <div className="card-header">
          <h1>SciFusion Live Job Tester</h1>
          <div className="header-bar">
            <button
              onClick={startJob}
              disabled={isConnecting || isJobRunning}
            >
              {isJobRunning ? "Job Running..." : "Start Test Job (3 Ideas)"}
            </button>
            <span className="status-badge" title={status}>
              Status: {status}
            </span>
          </div>
        </div>

        <div className="card-content">
          <div className="grid-container">

            {/* --- Column 1: Progress & Results --- */}
            <div className="grid-col-span-2">

              {/* THE MAIN PROGRESS BAR (Tracks Ideas) */}
              <JobProgressBar
                completed={ideasProcessed}
                total={totalExperiments}
              />

              <div className="card">
                <div className="card-header">
                  <h3>Experiment Results</h3>
                </div>
                <div className="card-content results-grid">
                  {!isJobRunning && novelIdeas.length === 0 && (
                    <p>Click "Start Test Job" to begin.</p>
                  )}
                  {isJobRunning && novelIdeas.length === 0 && (
                    <p>Waiting for novelty check to determine experiments...</p>
                  )}

                  {/* THE GROUPED RESULTS */}
                  {groupedExperiments.map((groupedExp) => (
                    <GroupedExperimentCard
                      key={groupedExp.idea.Name}
                      groupedExp={groupedExp}
                      baseline={baselineScore}
                    />
                  ))}
                </div>
              </div>
            </div>

            {/* --- Column 2: Logs & Data --- */}
            <div>
              <div className="card">
                <div className="card-header">
                  <h3>Live Log Feed</h3>
                </div>
                <div className="card-content">
                  <LogFeed logs={logFeed} />
                </div>
              </div>

              <div className="card">
                <div className="card-header">
                  <h3>Papers</h3>
                </div>
                <div className="card-content">
                  {papers ? (
                    <PrettyJson data={papers} />
                  ) : (
                    <p>Waiting for papers...</p>
                  )}
                </div>
              </div>
            </div>

          </div>
        </div>
      </div>
    </div>
  );
}