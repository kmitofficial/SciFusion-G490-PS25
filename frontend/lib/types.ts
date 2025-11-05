// Location: frontend/lib/types.ts

// --- Basic Types ---
export interface LogEntry {
    id: string; // We'll add this on the client
    timestamp: string;
    message: string;
    log_type: "info" | "success" | "fail" | "error" | "system";
}

// --- Paper Types ---
export interface Paper {
    id: string;
    paperId: string;
    title: string;
    year: number;
    citationCount: number;
    abstract: string;
    tldr: string | null;
    score: number;
}

export interface PaperBank {
    topic_description: string;
    all_queries: string[];
    paper_bank: Paper[];
    baseline_score?: number;
}

// --- Idea & Experiment Types (from your sample) ---
export interface Idea {
    Name: string;
    Title: string;
    Summary: string;
    id: string;
    description: string;
    score: number;
    [key: string]: any;
}

export interface ExperimentResult {
    idea_name: string;
    idea_title: string;
    run_number: number;
    metrics: any;
    folder_name: string;
    results_folder?: string;
    results_path?: string;
}

// --- Grouped Type for UI ---
export interface GroupedExperiment {
    idea: Idea;
    runs: ExperimentResult[];
}

// --- NEW: Full Job Type ---
export interface ResearchRequest {
    topic: string;
    experiment: string;
    model: string;
    code_model: string;
    num_ideas: number;
    rag: boolean;
    check_similarity: boolean;
    skip_novelty_check: boolean;
    round?: number;
    save_name?: string;
}

export interface Job {
    _id: string; // Comes from MongoDB as _id
    user_id: string;
    created_at: string;
    status: string;
    request: ResearchRequest;
    papers: PaperBank | null;
    ideas: Idea[] | null;
    experiment_results: ExperimentResult[];
    log: string | null;
    error_log: string | null;
}

export interface JobSidebarItem {
    _id?: string;
    id?: string;
    created_at: string;
    status: string;
    request?: {
        topic?: string;
    };
}

export interface ArtifactFolder {
    idea_name?: string;
    idea_title?: string;
    folder_name: string;
    folder_path: string;
}

export interface ArtifactNode {
    name: string;
    path: string;
    type: "file" | "directory";
    children?: ArtifactNode[];
}

export interface ArtifactFile {
    path: string;
    content: string;
}