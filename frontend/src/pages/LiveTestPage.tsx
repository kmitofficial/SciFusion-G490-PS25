import React, { useState, useEffect, useRef } from 'react';

// This is the TypeScript "shape" of our Job model from the backend
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
  ideas: object[] | null;
  experiment_results: any[];
  log: string | null;
  error_log: string | null;
}

// This is the shape of the WebSocket message
interface WebSocketMessage {
  type: "JOB_UPDATE" | "JOB_STARTED" | "ERROR";
  data: any;
}

// A simple component to render JSON nicely
const PrettyJson: React.FC<{ data: any }> = ({ data }) => (
  <pre className="json-pre">
    {JSON.stringify(data, null, 2)}
  </pre>
);

// Our main page component
export function LiveTestPage() {
  const [job, setJob] = useState<Job | null>(null);
  const [status, setStatus] = useState("Connecting to server...");
  const [isConnecting, setIsConnecting] = useState(true);
  const [isJobRunning, setIsJobRunning] = useState(false);
  const socket = useRef<WebSocket | null>(null);

  useEffect(() => {
    // This effect runs once to connect the WebSocket
    console.log("Connecting to WebSocket...");
    socket.current = new WebSocket("ws://localhost:8000/api/v1/ws");

    socket.current.onopen = () => {
      console.log("WebSocket connected!");
      setStatus("Connected. Ready to start a job.");
      setIsConnecting(false);
    };

    socket.current.onmessage = (event) => {
      const message: WebSocketMessage = JSON.parse(event.data);
      console.log("Received message:", message);

      if (message.type === "JOB_UPDATE") {
        const updatedJob: Job = message.data;
        setJob(updatedJob);
        setStatus(`Job status: ${updatedJob.status}`);
        if (updatedJob.status === 'complete' || updatedJob.status === 'failed') {
          setIsJobRunning(false);
        }
      } else if (message.type === "JOB_STARTED") {
        setStatus(`Job ${message.data.job_id} has started! Waiting for updates...`);
        setIsJobRunning(true);
      } else if (message.type === "ERROR") {
        setStatus(`Error: ${message.data}`);
        setIsJobRunning(false);
      }
    };

    socket.current.onclose = () => {
      console.log("WebSocket disconnected.");
      setStatus("Disconnected. Please refresh the page.");
      setIsConnecting(false);
      setIsJobRunning(false);
    };

    socket.current.onerror = (err) => {
      console.error("WebSocket error:", err);
      setStatus("Connection error. Is the backend server running?");
      setIsConnecting(false);
    };

    return () => {
      if (socket.current) {
        socket.current.close();
      }
    };
  }, []); // Empty array means this runs only once

  const startJob = () => {
    if (socket.current && socket.current.readyState === WebSocket.OPEN) {
      // This is the ResearchRequest object
      const researchRequest = {
        topic: "novel attention mechanisms for sentiment classification",
        experiment: "sentiment_classification_sst2",
        model: "gemini-2.5-flash-lite",
        code_model: "flash",
        num_ideas: 1, // Let's use 1 idea for a faster test
        rag: true,
        check_similarity: true,
        skip_novelty_check: true,
        round: 0,
        save_name: "frontend_test_job"
      };

      const message = {
        type: "START_JOB",
        payload: researchRequest,
      };

      console.log("Sending START_JOB message...");
      socket.current.send(JSON.stringify(message));

      setJob(null);
      setStatus("Job start message sent. Waiting for response...");
      setIsJobRunning(true);

    } else {
      setStatus("Not connected. Cannot start job.");
    }
  };

  return (
    <div className="container">
      <div className="card">
        <div className="card-header">
          <h1>SciFusion Live Job Tester (Bare Bones)</h1>
          <div className="header-bar">
            <button
              onClick={startJob}
              disabled={isConnecting || isJobRunning}
            >
              {isJobRunning ? "Job Running..." : "Start Test Job"}
            </button>
            <span className="status-badge">
              Status: {status}
            </span>
          </div>
        </div>

        <div className="card-content">
          {!job && isJobRunning && (
            <div className="alert">
              <div className="alert-title">Job in Progress</div>
              <p>Waiting for the first update from the server...</p>
            </div>
          )}

          {!job && !isJobRunning && !isConnecting && (
            <div className="alert">
              <div className="alert-title">Ready</div>
              <p>Click "Start Test Job" to begin a new research workflow.</p>
            </div>
          )}

          {job && (
            <div className="grid-container">
              <div className="card">
                <div className="card-header">
                  <h3>Papers</h3>
                </div>
                <div className="card-content">
                  {job.papers ? (
                    <PrettyJson data={job.papers} />
                  ) : (
                    <p>Waiting for papers...</p>
                  )}
                </div>
              </div>

              <div className="card">
                <div className="card-header">
                  <h3>Ideas</h3>
                </div>
                <div className="card-content">
                  {job.ideas ? (
                    <PrettyJson data={job.ideas} />
                  ) : (
                    <p>Waiting for ideas...</p>
                  )}
                </div>
              </div>

              <div className="card">
                <div className="card-header">
                  <h3>Experiment Results ({job.experiment_results.length})</h3>
                </div>
                <div className="card-content">
                  {job.experiment_results.length > 0 ? (
                    <PrettyJson data={job.experiment_results} />
                  ) : (
                    <p>Waiting for experiment results...</p>
                  )}
                </div>
              </div>

              <div className="card">
                <div className="card-header">
                  <h3>Full Job Document (Live)</h3>
                </div>
                <div className="card-content">
                  <PrettyJson data={job} />
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}