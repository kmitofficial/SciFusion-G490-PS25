import os.path as osp
import shutil
import json
import argparse
import multiprocessing
import torch
import os
import time
import sys
from dotenv import load_dotenv
import requests  # <-- NEW IMPORT

# --- AUTHENTICATION FIX ---
print("Loading environment variables from .env...")
load_dotenv()
if "GOOGLE_API_KEY" not in os.environ:
    print("[ERROR] GOOGLE_API_KEY not found in .env file. Please ensure it is set.")
    sys.exit(1)
# --- END AUTH FIX ---

from aider.coders import Coder
from aider.models import Model
from aider.io import InputOutput
from datetime import datetime
from dolphin_utils.generate_ideas import generate_ideas, check_idea_novelty
from dolphin_utils.experiments_utils import perform_experiments

NUM_REFLECTIONS = 3

# --- NEW API CALLBACK FUNCTIONS ---

# The base URL for our internal API
API_BASE_URL = "http://localhost:8000/api/v1"


def update_job_status(job_id, status):
    """Calls the internal API to update the job's high-level status."""
    if not job_id:
        return
    try:
        requests.post(
            f"{API_BASE_URL}/_internal/update-job-status/{job_id}",
            json={"status": status},
            timeout=5
        )
        print(f"[API_CALLBACK] Notified server: status = {status}")
    except Exception as e:
        print(f"[API_CALLBACK ERROR] Failed to update status: {e}")


def update_job_papers(job_id, papers_dict):
    """Calls the internal API to send the collected papers."""
    if not job_id:
        return
    try:
        requests.post(
            f"{API_BASE_URL}/_internal/update-papers/{job_id}",
            json=papers_dict,
            timeout=10
        )
        print("[API_CALLBACK] Notified server: papers collected")
    except Exception as e:
        print(f"[API_CALLBACK ERROR] Failed to send papers: {e}")


def update_job_ideas(job_id, ideas_list):
    """Calls the internal API to send the generated ideas."""
    if not job_id:
        return
    try:
        requests.post(
            f"{API_BASE_URL}/_internal/update-ideas/{job_id}",
            json=ideas_list,
            timeout=10
        )
        print("[API_CALLBACK] Notified server: ideas generated")
    except Exception as e:
        print(f"[API_CALLBACK ERROR] Failed to send ideas: {e}")


def push_experiment_result(job_id, result_dict):
    """Calls the internal API to push a single experiment result."""
    if not job_id:
        return
    try:
        requests.post(
            f"{API_BASE_URL}/_internal/push-result/{job_id}",
            json=result_dict,
            timeout=10
        )
        print(f"[API_CALLBACK] Notified server: pushed result for '{result_dict.get('idea_name', 'UKNOWN')}'")
    except Exception as e:
        print(f"[API_CALLBACK ERROR] Failed to push result: {e}")


# --- END API CALLBACK FUNCTIONS ---


def print_time():
    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


def parse_arguments():
    parser = argparse.ArgumentParser(description="Automatic Algorithm Design.")
    parser.add_argument("--skip-idea-generation", action="store_true",
                        help="Skip idea generation and load existing ideas")
    parser.add_argument("--skip-novelty-check", action="store_true", help="Skip novelty check and use existing ideas")
    parser.add_argument("--experiment", type=str, default="point_classification_modelnet",
                        help="Experiment to run AutoAD on.")
    parser.add_argument("--model", type=str, default="gemini-2.5-flash-lite", help="Model to use for AutoAD.")
    parser.add_argument("--code_model", type=str, default="flash",
                        help="Model to use for experimental implementation.")
    parser.add_argument("--parallel", type=int, default=0,
                        help="Number of parallel processes to run. 0 for sequential execution.")
    parser.add_argument("--gpus", type=str, default=None,
                        help="Comma-separated list of GPU IDs to use (e.g., '0,1,2'). If not specified, all available GPUs will be used.")
    parser.add_argument("--rag", action="store_true", help="Use RAG to generate ideas.")
    parser.add_argument("--topic", type=str, default=None, help="Topic for RAG.")
    parser.add_argument("--seed", type=int, default=2025, help="Random seed.")
    parser.add_argument("--max_papers", type=int, default=20, help="Number of rag papers.")
    parser.add_argument("--memory_papers", type=int, default=10, help="Use memory papers to generate the next query.")
    parser.add_argument("--num-ideas", type=int, default=20, help="Number of ideas to generate")
    parser.add_argument("--check_similarity", action="store_true", help="check similarity when generate ideas")
    parser.add_argument("--embedding_model", type=str, default="sentence-transformers/all-roberta-large-v1",
                        help="embedding model to check similarity")
    parser.add_argument("--round", type=int, default=0, help="Round of experiments")
    parser.add_argument("--save_name", type=str, default=None, help="Result dir (default: results/exp_name)")

    # --- MODIFIED: Added job-id ---
    parser.add_argument("--job-id", type=str, default="007", help="Job ID for saving results via API callback")

    return parser.parse_args()


def get_available_gpus(gpu_ids=None):
    if gpu_ids is not None:
        try:
            return [int(gpu_id) for gpu_id in gpu_ids.split(',')]
        except ValueError:
            print(f"[ERROR] Invalid GPU IDs specified: {gpu_ids}. Using all available GPUs.")
    return list(range(torch.cuda.device_count()))


def bootstrap_experiment(base_dir, topic):
    """
    Checks if a new experiment directory has the required files.
    If not, it creates default placeholders to prevent errors.
    """
    print(f"[PROCESS] Bootstrapping: Checking project structure in {base_dir}...")

    seed_ideas_path = osp.join(base_dir, "seed_ideas.json")
    prompt_path = osp.join(base_dir, "prompt.json")
    experiment_path = osp.join(base_dir, "experiment.py")
    run_0_dir = osp.join(base_dir, "run_0")
    baseline_info_path = osp.join(run_0_dir, "final_info.json")
    baseline_script_path = osp.join(run_0_dir, "experiment.py")

    description = topic if topic else "A new AutoAD experiment"
    if topic:
        print(f"[PROCESS] Bootstrapping: Using topic for description: {topic}")

    default_experiment_code = (
        "# This is a placeholder experiment file.\n"
        "# The AI will modify this file to implement ideas.\n"
        "import torch\n\n"
        "def main():\n"
        "    print('Baseline experiment script.')\n\n"
        "if __name__ == '__main__':\n"
        "    main()\n"
    )

    # Create seed_ideas.json if it's missing
    if not osp.exists(seed_ideas_path):
        print(f"[PROCESS] Bootstrapping: Creating missing file: {seed_ideas_path}")
        default_seed_ideas = [
            {
                "Name": "Baseline",
                "Title": "Baseline Experiment",
                "Summary": description,
                "Experiment": "Establish baseline performance for the task.",
                "Method": "Baseline implementation."
            }
        ]
        with open(seed_ideas_path, "w") as f:
            json.dump(default_seed_ideas, f, indent=4)

    # Create prompt.json if it's missing
    if not osp.exists(prompt_path):
        print(f"[PROCESS] Bootstrapping: Creating missing file: {prompt_path}")
        default_prompt = {
            "system": "You are an AI research assistant. Your goal is to design novel machine learning algorithms.",
            "task_description": description
        }
        with open(prompt_path, "w") as f:
            json.dump(default_prompt, f, indent=4)

    # Create root experiment.py if it's missing
    if not osp.exists(experiment_path):
        print(f"[PROCESS] Bootstrapping: Creating missing file: {experiment_path}")
        with open(experiment_path, "w") as f:
            f.write(default_experiment_code)

    # Ensure run_0 directory exists
    os.makedirs(run_0_dir, exist_ok=True)

    # Create dummy baseline results in run_0 if missing
    if not osp.exists(baseline_info_path):
        print(f"[PROCESS] Bootstrapping: Creating missing file: {baseline_info_path}")
        default_baseline_results = {
            "baseline_metric": {
                "means": [0.0],
                "stds": [0.0]
            }
        }
        with open(baseline_info_path, "w") as f:
            json.dump(default_baseline_results, f, indent=4)

    # Create baseline script in run_0 if missing
    if not osp.exists(baseline_script_path):
        print(f"[PROCESS] Bootstrapping: Creating missing file: {baseline_script_path}")
        with open(baseline_script_path, "w") as f:
            f.write(default_experiment_code)

    print(f"[PROCESS] Bootstrapping: Check complete. All required files are in place.")


# --- MODIFIED: Added job_id parameter ---
def worker(queue, base_dir, results_dir, model, client, client_model, writeup, improvement, gpu_id, job_id):
    os.environ["CUDA_VISIBLE_DEVICES"] = str(gpu_id)
    print(f"[PROCESS] Worker {gpu_id} started.")
    while True:
        idea = queue.get()
        if idea is None:
            break
        print(f"[PROCESS] Worker {gpu_id} picked up idea: {idea.get('Name', 'Unnamed Idea')}")
        success = do_idea(
            base_dir, results_dir, idea, model, client, client_model, writeup, improvement, job_id, log_file=True
        )
        print(f"[PROCESS] Worker {gpu_id} completed idea: {idea.get('Name', 'Unnamed Idea')}, Success: {success}")
    print(f"[PROCESS] Worker {gpu_id} finished.")


# --- MODIFIED: Added job_id parameter ---
def do_idea(base_dir, results_dir, idea, model, job_id, log_file=False):
    ## CREATE PROJECT FOLDER
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    idea_name_safe = idea.get('Name', 'Unnamed_Idea').replace(' ', '_').replace('/', '_')
    idea_name = f"{timestamp}_{idea_name_safe}"
    folder_name = osp.join(results_dir, idea_name)
    print(f"[PROCESS] do_idea: Creating project folder: {folder_name}")

    # Handle potential file name too long error
    if len(folder_name) > 255:
        folder_name = osp.join(results_dir, f"{timestamp}_{idea_name_safe[:50]}")
        print(f"[PROCESS] do_idea: Folder name too long, shortening to: {folder_name}")

    assert not osp.exists(folder_name), f"Folder {folder_name} already exists."
    destination_dir = folder_name
    shutil.copytree(base_dir, destination_dir, dirs_exist_ok=True)

    print(f"[PROCESS] do_idea: Loading baseline results from {osp.join(base_dir, 'run_0', 'final_info.json')}")
    with open(osp.join(base_dir, "run_0", "final_info.json"), "r") as f:
        baseline_results = json.load(f)
    baseline_results = {k: v["means"] for k, v in baseline_results.items()}
    print(f"[PROCESS] do_idea: Baseline results loaded: {baseline_results}")

    exp_file = osp.join(folder_name, "experiment.py")
    notes = osp.join(folder_name, "notes.txt")

    print(f"[PROCESS] do_idea: Writing notes.txt")
    with open(notes, "w") as f:
        f.write(f"# Title: {idea['Title']}\n")
        f.write(f"# Experiment description: {idea['Experiment']}\n")
        f.write(f"## Run 0: Baseline\n")
        f.write(f"Results: {baseline_results}\n")
        f.write(f"Description: Baseline results.\n")

    if log_file:
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        log_path = osp.join(folder_name, "log.txt")
        print(f"[PROCESS] do_idea: Redirecting stdout/stderr to log file: {log_path}")
        try:
            log = open(log_path, "a", encoding='utf-8')
            sys.stdout = log
            sys.stderr = log
        except Exception as e:
            print(f"Error opening log file: {e}. Logging to console.")
            log_file = False  # Fallback to console

    try:
        print_time()
        print(f"*Starting idea: {idea_name}*")
        ## PERFORM EXPERIMENTS
        fnames = [exp_file, notes]
        print(f"[PROCESS] do_idea: Initializing InputOutput for aider.")
        io = InputOutput(yes=True, chat_history_file=f"{folder_name}/{idea_name_safe}_aider.txt")

        print(f"[PROCESS] do_idea: Initializing model for Coder: {model}")

        if model.startswith("deepseek"):
            main_model = Model("deepseek/deepseek-coder")
        elif model.startswith("localhost"):
            ollama_model = "ollama/" + "-".join(model.split("-")[1:])
            main_model = Model(ollama_model)
        else:
            main_model = Model(model)

        print(f"[PROCESS] do_idea: Creating Coder with files: {fnames}")
        coder = Coder.create(
            main_model=main_model, fnames=fnames, io=io, stream=False, use_git=False, edit_format="diff"
        )

        print_time()
        print(f"*Starting Experiments*")
        try:
            print(f"[PROCESS] do_idea: Calling perform_experiments...")
            success = perform_experiments(idea, folder_name, coder, baseline_results)
            print(f"[PROCESS] do_idea: perform_experiments finished. Success: {success}")
        except Exception as e:
            print(f"Error during experiments: {e}")
            print(f"Experiments failed for idea {idea_name}")
            return False

        if not success:
            print(f"Experiments failed for idea {idea_name}")
            return False

        # --- MODIFIED: Save result via API callback ---
        print_time()
        print(f"*Experiment {idea_name} Succeeded. Saving results to API.*")
        try:
            result_path = osp.join(folder_name, "final_info.json")
            if not osp.exists(result_path):
                print(f"[API_CALLBACK ERROR] final_info.json not found at {result_path}")
            else:
                with open(result_path, "r") as f:
                    result_data = json.load(f)

                experiment_result = {
                    "idea_name": idea.get("Name", "Unnamed Idea"),
                    "idea_title": idea.get("Title", "Untitled"),
                    "metrics": result_data,
                    "folder_name": os.path.basename(folder_name)
                }

                # Call our new API helper function
                push_experiment_result(job_id, experiment_result)

        except Exception as e:
            print(f"[API_CALLBACK ERROR] Failed to save experiment result via API: {e}")
        # --- END MODIFICATION ---

        print_time()
        return True  # Explicitly return True

    except Exception as e:
        print(f"Failed to evaluate idea {idea_name}: {str(e)}")
        return False
    finally:
        print("FINISHED IDEA")
        if log_file and 'log' in locals() and not log.closed:
            print(f"[PROCESS] do_idea: Restoring stdout/stderr.")
            sys.stdout = original_stdout
            sys.stderr = original_stderr
            log.close()


def check_results(exp_base_dir):
    all_exp = os.listdir(exp_base_dir)


if __name__ == "__main__":
    print(f"[PROCESS] --- Script Start ---")
    args = parse_arguments()
    print(f"[PROCESS] Arguments parsed: {args}")

    # --- MODIFIED: Notify server that script is running ---
    update_job_status(args.job_id, "running")
    # --- END MODIFICATION ---

    print(f"[PROCESS] Checking available GPUs...")
    available_gpus = get_available_gpus(args.gpus)
    if args.parallel > len(available_gpus):
        print(
            f"Warning: Requested {args.parallel} parallel processes, but only {len(available_gpus)} GPUs available. Adjusting to {len(available_gpus)}."
        )
        args.parallel = len(available_gpus)

    print(f"[PROCESS] Using GPUs: {available_gpus}")
    print(f"[PROCESS] Parallel processes: {args.parallel}")

    print(f"[PROCESS] Creating LLM client for model: {args.model}")
    if "claude" in args.model:
        import anthropic

        client_model = args.model
        client = anthropic.Anthropic()
    elif args.model in ["openai/gpt-oss-120b",
                        "openai/gpt-oss-20b"] or "groq" in args.model.lower() or args.model.startswith("openai/"):
        import groq

        client_model = args.model
        client = groq.Groq(api_key=os.environ.get("GROQ_API_KEY"))
    elif "gpt" in args.model and not args.model.startswith("openai/"):
        import openai

        client_model = args.model
        client = openai.OpenAI()
    elif "deepseek" in args.model:
        import openai

        client_model = args.model
        client = openai.OpenAI(api_key=os.environ["DEEPSEEK_API_KEY"], base_url="https://api.deepseek.com")
    elif args.model == "Intern-S1":
        import openai

        client_model = args.model
        client = openai.OpenAI(api_key=os.environ["INS1_API_KEY"], base_url="https://chat.intern-ai.org.cn/api/v1/")
    elif args.model.startswith("localhost"):
        import openai

        client_model = args.model
        client = openai.OpenAI(base_url="http://localhost:11434/v1", api_key="na")
    elif args.model.startswith("gemini"):
        import google.generativeai as genai

        if "GOOGLE_API_KEY" not in os.environ:
            print("[ERROR] GOOGLE_API_KEY not found, but gemini model was requested for main client.")
            sys.exit(1)
        genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
        client = genai.GenerativeModel(args.model)
        client_model = args.model
    else:
        raise ValueError(f"Model {args.model} is not supported.")

    print(f"[PROCESS] LLM Client created successfully.")

    base_dir = osp.join("examples", args.experiment)
    print(f"[PROCESS] Base experiment directory set to: {base_dir}")

    if args.save_name:
        results_dir = osp.join("results", args.save_name)
    else:
        results_dir = osp.join("results", args.experiment)
    print(f"[PROCESS] Results directory set to: {results_dir}")

    os.makedirs(base_dir, exist_ok=True)
    os.makedirs(results_dir, exist_ok=True)

    print(f"[PROCESS] Calling bootstrap function...")
    bootstrap_experiment(base_dir, args.topic)

    if args.round > 0:
        print(f"[PROCESS] Round {args.round}: Looking for results from previous round.")
        # ... (same logic as before) ...
    else:
        exp_base_file_list = None

    if args.rag:
        print(f"[PROCESS] RAG is enabled.")
        from dolphin_utils.rag_tools.lit_review import collect_papers

        assert args.topic is not None, "Topic must be provided for RAG."
        print(f"[PROCESS] RAG: Collecting papers for topic: {args.topic}")
        paper_bank, total_cost, all_queries = collect_papers(
            args.topic, client, client_model, args.seed, args.memory_papers, args.max_papers
        )
        print(f"[PROCESS] RAG: Collected {len(paper_bank)} papers. Total cost: {total_cost}")

        paper_dict = {
            "topic_description": args.topic,
            "all_queries": all_queries,
            "paper_bank": paper_bank
        }

        # --- MODIFIED: Save to file AND send to API ---
        file_path = osp.join(base_dir, f"{args.experiment}_rag_papers.json")
        print(f"[PROCESS] RAG: Saving paper bank to {file_path}")
        with open(file_path, "w") as f:
            json.dump(paper_dict, f, indent=4)

        update_job_papers(args.job_id, paper_dict)
        # --- END MODIFICATION ---
    else:
        print(f"[PROCESS] RAG is disabled.")

    print(f"[PROCESS] Calling generate_ideas...")
    ideas = generate_ideas(
        base_dir,
        client=client,
        model=client_model,
        skip_generation=args.skip_idea_generation,
        max_num_generations=args.num_ideas,
        num_reflections=NUM_REFLECTIONS,
        rag=args.rag,
        rag_path=osp.join(base_dir, f"{args.experiment}_rag_papers.json"),
        check_independence=args.check_similarity,
        embedding_model=args.embedding_model,
        round=args.round,
        exp_base_file_list=exp_base_file_list,
    )
    print(f"[PROCESS] generate_ideas finished. Found {len(ideas)} ideas.")

    # --- MODIFIED: Send ideas to API ---
    update_job_ideas(args.job_id, ideas)
    # --- END MODIFICATION ---

    if args.skip_novelty_check:
        print(f"[PROCESS] Skipping novelty check.")
        for idea in ideas:
            idea["novel"] = True
            idea["independence"] = True
    else:
        print(f"[PROCESS] Calling check_idea_novelty...")
        ideas = check_idea_novelty(
            ideas,
            base_dir=base_dir,
            client=client,
            model=client_model,
            round=args.round
        )
        print(f"[PROCESS] check_idea_novelty finished.")

    filter_ideas = [idea for idea in ideas if idea.get('independence', True)]
    print(f"[PROCESS] Filtered for independence: {len(filter_ideas)} ideas remaining.")
    novel_ideas = [idea for idea in filter_ideas if idea.get("novel", False)]
    print(f"Run experiments on {len(novel_ideas)} novel and independent ideas.")

    if args.parallel > 0:
        print(f"[PROCESS] Starting PARALLEL execution with {args.parallel} processes.")
        queue = multiprocessing.Queue()
        for idea in novel_ideas:
            queue.put(idea)

        processes = []
        for i in range(args.parallel):
            gpu_id = available_gpus[i % len(available_gpus)]
            print(f"[PROCESS] Starting worker {i} on GPU {gpu_id}")
            p = multiprocessing.Process(
                target=worker,
                args=(
                    queue,
                    base_dir,
                    results_dir,
                    args.code_model,
                    # --- MODIFIED: Pass job_id to worker ---
                    gpu_id,
                    args.job_id
                )
            )
            p.start()
            time.sleep(150)
            processes.append(p)

        print(f"[PROCESS] All workers started. Adding {args.parallel} None signals to queue.")
        for _ in range(args.parallel):
            queue.put(None)

        print(f"[PROCESS] Waiting for all workers to join...")
        for p in processes:
            p.join()

        print("[PROCESS] All parallel processes completed.")
    else:
        print(f"[PROCESS] Starting SEQUENTIAL execution.")
        # --- MODIFIED: Notify server ---
        update_job_status(args.job_id, "experiments_running")
        # --- END MODIFICATION ---

        for i, idea in enumerate(novel_ideas):
            print(f"[PROCESS] --- Processing idea {i + 1}/{len(novel_ideas)} (Sequential) ---")
            print(f"Processing idea: {idea['Name']}")
            try:
                # --- MODIFIED: Pass job_id ---
                success = do_idea(
                    base_dir,
                    results_dir,
                    idea,
                    args.code_model,
                    args.job_id
                )
                print(f"Completed idea: {idea['Name']}, Success: {success}")
            except Exception as e:
                print(f"Failed to evaluate idea {idea['Name']}: {str(e)}")
            print(f"[PROCESS] --- Finished idea {i + 1}/{len(novel_ideas)} ---")

    print("[PROCESS] All ideas evaluated.")

    # --- MODIFIED: Notify server of completion ---
    update_job_status(args.job_id, "complete")
    # --- END MODIFICATION ---

    print(f"[PROCESS] --- Script End ---")