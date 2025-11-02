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

# --- AUTHENTICATION FIX ---
# Load .env file *first* to get all keys.
print("Loading environment variables from .env...")
load_dotenv()
if "GOOGLE_API_KEY" not in os.environ:
    print("[ERROR] GOOGLE_API_KEY not found in .env file. Please ensure it is set.")
    sys.exit(1)
if "OPENROUTER_API_KEY" not in os.environ:
    print("[ERROR] OPENROUTER_API_KEY not found in .env file. Please ensure it is set for the --code_model.")
    sys.exit(1)
else:
    print("[PROCESS] Top-level: Found OPENROUTER_API_KEY.")
# --- END AUTH FIX ---

from aider.coders import Coder
from aider.models import Model
from aider.io import InputOutput
from datetime import datetime
from dolphin_utils.generate_ideas import generate_ideas, check_idea_novelty
from dolphin_utils.experiments_utils import perform_experiments

NUM_REFLECTIONS = 3


def print_time():
    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


def parse_arguments():
    parser = argparse.ArgumentParser(description="Automatic Algorithm Design.")
    parser.add_argument("--skip-idea-generation", action="store_true",
                        help="Skip idea generation and load existing ideas")
    parser.add_argument("--skip-novelty-check", action="store_true", help="Skip novelty check and use existing ideas")
    parser.add_argument("--experiment", type=str, default="point_classification_modelnet",
                        help="Experiment to run AutoAD on.")
    parser.add_argument("--model", type=str, default="claude-3-5-sonnet-20240620", help="Model to use for AutoAD.")
    parser.add_argument("--code_model", type=str, default="deepseek",
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
    baseline_script_path = osp.join(run_0_dir, "experiment.py")  # <-- Path for the baseline script

    # Use topic if provided, otherwise a generic fallback
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
                "Method": "Baseline implementation."  # <-- FIX FOR Error 1
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

    # --- CORRECTED BOOTSTRAP FIX ---
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
    # --- END OF FIX ---

    print(f"[PROCESS] Bootstrapping: Check complete. All required files are in place.")


def worker(queue, base_dir, results_dir, model, client, client_model, writeup, improvement, gpu_id):
    os.environ["CUDA_VISIBLE_DEVICES"] = str(gpu_id)
    print(f"[PROCESS] Worker {gpu_id} started.")
    while True:
        idea = queue.get()
        if idea is None:
            break
        print(f"[PROCESS] Worker {gpu_id} picked up idea: {idea.get('Name', 'Unnamed Idea')}")
        success = do_idea(
            base_dir, results_dir, idea, model, client, client_model, writeup, improvement, log_file=True
        )
        print(f"[PROCESS] Worker {gpu_id} completed idea: {idea.get('Name', 'Unnamed Idea')}, Success: {success}")
    print(f"[PROCESS] Worker {gpu_id} finished.")


def do_idea(base_dir, results_dir, idea, model, log_file=False):
    ## CREATE PROJECT FOLDER
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    idea_name = f"{timestamp}_{idea['Name']}"
    folder_name = osp.join(results_dir, idea_name)
    print(f"[PROCESS] do_idea: Creating project folder: {folder_name}")
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
        f.write(f"# Method: {idea.get('Method', 'N/A')}\n") # <-- Safety net for 'Method' key
        f.write(f"# Experiment description: {idea['Experiment']}\n")
        f.write(f"## Run 0: Baseline\n")
        f.write(f"Results: {baseline_results}\n")
        f.write(f"Description: Baseline results.\n")

    if log_file:
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        log_path = osp.join(folder_name, "log.txt")
        print(f"[PROCESS] do_idea: Redirecting stdout/stderr to log file: {log_path}")
        log = open(log_path, "a")
        sys.stdout = log
        sys.stderr = log

    try:
        print_time()
        print(f"*Starting idea: {idea_name}*")
        ## PERFORM EXPERIMENTS
        # fnames = [model_file, train_file, notes]
        fnames = [exp_file, notes]
        print(f"[PROCESS] do_idea: Initializing InputOutput for aider.")
        io = InputOutput(yes=True, chat_history_file=f"{folder_name}/{idea_name}_aider.txt")

        # --- This is the original, correct code ---
        # Aider will read the OPENROUTER_API_KEY from the environment
        # (which we loaded at the top of the script)
        # when it sees a model name like "openrouter/..."

        print(f"[PROCESS] do_idea: Initializing model for Coder: {model}")

        if model.startswith("deepseek"):
            main_model = Model("deepseek/deepseek-coder")
        elif model.startswith("localhost"):
            ollama_model = "ollama/" + "-".join(model.split("-")[1:])
            main_model = Model(ollama_model)
        else:
            main_model = Model(model)  # This will now work for "openrouter/qwen/qwen3-coder:free"
        # --- End of fix ---

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

        print_time()
    except Exception as e:
        print(f"Failed to evaluate idea {idea_name}: {str(e)}")
        return False
    finally:
        print("FINISHED IDEA")
        if log_file:
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

    # Check available GPUs and adjust parallel processes if necessary
    print(f"[PROCESS] Checking available GPUs...")
    available_gpus = get_available_gpus(args.gpus)
    if args.parallel > len(available_gpus):
        print(
            f"Warning: Requested {args.parallel} parallel processes, but only {len(available_gpus)} GPUs available. Adjusting to {len(available_gpus)}."
        )
        args.parallel = len(available_gpus)

    print(f"[PROCESS] Using GPUs: {available_gpus}")
    print(f"[PROCESS] Parallel processes: {args.parallel}")

    # Create client
    print(f"[PROCESS] Creating LLM client for model: {args.model}")
    if "claude" in args.model:
        import anthropic

        print(f"Using Anthropic API with model {args.model}.")
        client_model = args.model
        client = anthropic.Anthropic()
    elif args.model in ["openai/gpt-oss-120b",
                        "openai/gpt-oss-20b"] or "groq" in args.model.lower() or args.model.startswith("openai/"):
        import groq

        print(f"Using Groq API with model {args.model}.")
        client_model = args.model
        client = groq.Groq(
            api_key=os.environ.get("GROQ_API_KEY")  # This is for the *main* client
        )
    elif "gpt" in args.model and not args.model.startswith("openai/"):
        import openai

        print(f"Using OpenAI API with model {args.model}.")
        client_model = args.model
        client = openai.OpenAI()
    elif "deepseek" in args.model:
        import openai

        print(f"Using DeepSeek API with {args.model}.")
        client_model = args.model
        client = openai.OpenAI(
            api_key=os.environ["DEEPSEEK_API_KEY"],
            base_url="https://api.deepseek.com"
        )
    elif args.model == "Intern-S1":
        import openai

        print(f"Using OpenAI API with model {args.model}.")
        client_model = args.model
        client = openai.OpenAI(
            api_key=os.environ["INS1_API_KEY"],
            base_url="https://chat.intern-ai.org.cn/api/v1/"
        )
    elif args.model.startswith("localhost"):
        import openai

        print(f"Using OpenAI API with locally deployed model: {args.model}.")
        client_model = args.model
        client = openai.OpenAI(base_url="http://localhost:11434/v1", api_key="na")
    elif args.model.startswith("gemini"):
        import google.generativeai as genai

        print(f"Using Google Gemini API with model {args.model}.")
        # This line requires GOOGLE_API_KEY to be in the environment (which we loaded at the top)
        if "GOOGLE_API_KEY" not in os.environ:
            print("[ERROR] GOOGLE_API_KEY not found, but gemini model was requested for main client.")
            sys.exit(1)
        genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
        client = genai.GenerativeModel(args.model)
        client_model = args.model
    else:
        # This will handle OpenRouter for the *main* client, if you ever want to do that.
        # But for now, we only need OpenRouter for the --code_model.
        print(f"Using model {args.model}, assuming it's supported by a loaded API key (like OpenRouter).")
        import openai
        client = openai.OpenAI(
            base_url = "https://openrouter.ai/api/v1",
            api_key = os.environ.get("OPENROUTER_API_KEY")
        )
        client_model = args.model

    print(f"[PROCESS] LLM Client created successfully.")

    # Build directories
    base_dir = osp.join("examples", args.experiment)
    print(f"[PROCESS] Base experiment directory set to: {base_dir}")

    if args.save_name:
        results_dir = osp.join("results", args.save_name)
    else:
        results_dir = osp.join("results", args.experiment)
    print(f"[PROCESS] Results directory set to: {results_dir}")

    os.makedirs(base_dir, exist_ok=True)
    os.makedirs(results_dir, exist_ok=True)

    # Call the bootstrap function to create default files if they don't exist
    print(f"[PROCESS] Calling bootstrap function...")
    bootstrap_experiment(base_dir, args.topic)

    # FIX for Round > 0
    if args.round > 0:
        print(f"[PROCESS] Round {args.round}: Looking for results from previous round.")
        prev_round = args.round - 1
        prev_ideas_file = osp.join(base_dir, f"ideas_round_{prev_round}_with_pos.json")

        # Check if the results directory from the previous run exists
        if not osp.exists(results_dir):
            print(f"[ERROR] results_dir {results_dir} does not exist. Cannot find previous results to learn from.")
            sys.exit(1)

        # Check if the ideas file from the previous round exists
        if not osp.exists(prev_ideas_file):
            print(f"[ERROR] Previous ideas file {prev_ideas_file} not found.")
            print(f"       You must run round {prev_round} successfully before running round {args.round}.")
            sys.exit(1)

        # exp_base_file_list[0] = list of result directories to check
        # exp_base_file_list[1] = list of idea files to load
        exp_base_file_list = ([results_dir], [prev_ideas_file])
        print(f"[PROCESS] Found previous round data. Using ideas from: {prev_ideas_file}")
        print(f"[PROCESS] Will check for experiment results in: {results_dir}")
    else:
        exp_base_file_list = None
    # --- End of Fix ---

    if args.rag:
        print(f"[PROCESS] RAG is enabled.")
        from dolphin_utils.rag_tools.lit_review import collect_papers

        assert args.topic is not None, "Topic must be provided for RAG."
        print(f"[PROCESS] RAG: Collecting papers for topic: {args.topic}")
        # Collect papers
        paper_bank, total_cost, all_queries = collect_papers(
            args.topic, client, client_model, args.seed, args.memory_papers, args.max_papers
        )
        print(f"[PROCESS] RAG: Collected {len(paper_bank)} papers. Total cost: {total_cost}")

        # Prepare dictionary
        paper_dict = {
            "topic_description": args.topic,
            "all_queries": all_queries,
            "paper_bank": paper_bank
        }

        file_path = osp.join(base_dir, f"{args.experiment}_rag_papers.json")
        print(f"[PROCESS] RAG: Saving paper bank to {file_path}")
        with open(file_path, "w") as f:
            json.dump(paper_dict, f, indent=4)
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

    if args.skip_novelty_check:
        print(f"[PROCESS] Skipping novelty check.")
        # If we skip the check, we must manually mark all ideas as novel and independent
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

    filter_ideas = [idea for idea in ideas if idea.get('independence', True)]  # Default to True if key missing
    print(f"[PROCESS] Filtered for independence: {len(filter_ideas)} ideas remaining.")
    novel_ideas = [idea for idea in filter_ideas if idea.get("novel", False)]  # Default to False if key missing
    print(f"[PROCESS] Filtered for novelty: {len(novel_ideas)} ideas remaining.")
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
                    gpu_id,
                )
            )
            p.start()
            time.sleep(150)  # Stagger worker starts
            processes.append(p)

        # Signal workers to exit
        print(f"[PROCESS] All workers started. Adding {args.parallel} None signals to queue.")
        for _ in range(args.parallel):
            queue.put(None)

        # Wait for all processes to finish
        print(f"[PROCESS] Waiting for all workers to join...")
        for p in processes:
            p.join()

        print("[PROCESS] All parallel processes completed.")
    else:
        print(f"[PROCESS] Starting SEQUENTIAL execution.")
        for i, idea in enumerate(novel_ideas):
            print(f"[PROCESS] --- Processing idea {i + 1}/{len(novel_ideas)} (Sequential) ---")
            print(f"Processing idea: {idea['Name']}")
            try:
                success = do_idea(
                    base_dir,
                    results_dir,
                    idea,
                    args.code_model
                )
                print(f"Completed idea: {idea['Name']}, Success: {success}")
            except Exception as e:
                print(f"Failed to evaluate idea {idea['Name']}: {str(e)}")
            print(f"[PROCESS] --- Finished idea {i + 1}/{len(novel_ideas)} ---")

    print("[PROCESS] All ideas evaluated.")
    print(f"[PROCESS] --- Script End ---")