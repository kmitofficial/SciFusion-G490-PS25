import shutil
import os.path as osp
import subprocess
from subprocess import TimeoutExpired
import sys
import json
import re
import os
from dolphin_utils.prompts import *
import filecmp
import requests  # <-- NEW IMPORT

MAX_ITERS = 4
MAX_RUNS = 5
MAX_STDERR_OUTPUT = 3000

# ---
# --- NEW: Copied from launch_dolphin.py to send results from here
# ---
API_BASE_URL = "http://localhost:8000/api/v1"


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


# ---
# --- END NEW
# ---


# return (file, line, function, content), message
def info_traceback(stderr):
    pattern = r'File "(.*)", line (\d+), in (.+)\n (.*)'
    matches = re.findall(pattern, stderr)
    match = re.search(rf'\w*Error\w*(.*)', stderr, re.DOTALL)
    if match:
        message = match.group(1).strip()
    else:
        message = stderr  # Fallback if no Error pattern found
    externel = []
    for match in matches:
        if match[0].split('/')[-1] == 'experiment.py':
            continue
        else:
            externel.append(match)
    for e in externel:
        matches.remove(e)

    return matches, message


# RUN EXPERIMENT
# --- MODIFIED: Added job_id and idea ---
def run_experiment(folder_name, run_num, job_id, idea, timeout=18000):
    cwd = osp.abspath(folder_name)
    # COPY CODE SO WE CAN SEE IT.
    if osp.exists(osp.join(cwd, f"run_{run_num}")):
        shutil.copy(osp.join(cwd, "experiment.py"), osp.join(cwd, f"run_{run_num}", "experiment.py"))
    else:
        os.mkdir(osp.join(cwd, f"run_{run_num}"))
        shutil.copy(osp.join(cwd, "experiment.py"), osp.join(cwd, f"run_{run_num}", "experiment.py"))

    # LAUNCH COMMAND
    command = ["bash", "launcher.sh", f"run_{run_num}"]
    try:
        result = subprocess.run(
            command, cwd=cwd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True, timeout=timeout
        )

        # --- THIS IS THE CRITICAL CHANGE ---
        # --- We check for a result file *regardless* of return code,
        # --- as Aider might fail but still produce a (failed) result.
        # ---
        if os.path.exists(osp.join(cwd, f"run_{run_num}", "final_info.json")):
            results = {}  # This dict is for the *next prompt*, not the websocket

            baseline_path = osp.join(cwd, "run_0", "final_info.json")
            if os.path.exists(baseline_path):
                with open(baseline_path, "r") as f:
                    baseline_data = json.load(f)
                baseline_results = {k: v["means"] for k, v in baseline_data.items()}
                results["baseline"] = baseline_results

            for run_idx in range(1, run_num + 1):
                run_path = osp.join(cwd, f"run_{run_idx}", "final_info.json")
                if os.path.exists(run_path):
                    with open(run_path, "r") as f:
                        run_data = json.load(f)

                    # ---
                    # --- THIS IS THE FIX ---
                    # --- Send a WebSocket message for EACH run that completes
                    # ---
                    if run_idx == run_num:  # Only send the result for the run that *just* finished
                        print(f"[PROCESS] Run {run_num} complete, sending result to API.")
                        experiment_result = {
                            "idea_name": idea.get('Name', 'Unnamed Idea'),  # <-- ORIGINAL Name
                            "idea_title": idea.get('Title', 'Untitled'),  # <-- ORIGINAL Title
                            "run_number": run_num,  # <-- NEW FIELD
                            "metrics": run_data,
                            "folder_name": f"{os.path.basename(folder_name)}_run_{run_num}"  # Make a unique ID
                        }
                        push_experiment_result(job_id, experiment_result)
                    # ---
                    # --- END FIX
                    # ---

                    run_results = {k: v["means"] for k, v in run_data.items()}
                    results[f"improve_{run_idx}"] = run_results

            next_prompt = next_experiment_prompt.format(RUN_NUM=run_num, RESULTS=results, NEXT_RUN_NUM=run_num + 1)

            # If we got here, the run *produced a file*, so it's a "success" for Aider
            # Even if the metrics are bad. Aider will decide what to do next.
            traceback, message, tb = None, None, None
            return 0, next_prompt, traceback, message  # <-- Return 0 (success)

        # --- IF NO final_info.json was found ---

        tb = None
        traceback = None
        message = None
        traceback_path = osp.join(cwd, f"run_{run_num}", "traceback.log")

        if result.stderr:
            print(result.stderr, file=sys.stderr)
            if osp.exists(traceback_path):
                with open(traceback_path, "r") as file:
                    tb = file.read()
                traceback, message = info_traceback(tb)
            else:
                print(f"[PROCESS] run_experiment: stderr was present, but no traceback.log found at {traceback_path}.")
                tb = result.stderr
                traceback, message = info_traceback(tb)

        if result.returncode != 0:
            print(f"Run {run_num} failed with return code {result.returncode}")
            if osp.exists(osp.join(cwd, f"run_{run_num}")):
                shutil.rmtree(osp.join(cwd, f"run_{run_num}"))
            print(f"Run failed with the following error {result.stderr}")
            if tb:
                stderr_output = tb
            else:
                stderr_output = result.stderr
            if len(stderr_output) > MAX_STDERR_OUTPUT:
                stderr_output = "..." + stderr_output[-MAX_STDERR_OUTPUT:]
            next_prompt = f"Run failed with the following error {stderr_output}"
        else:
            print(f"Run {run_num} succeeded (code 0) but final_info.json was not found.")
            next_prompt = "Run succeeded (return code 0) but no 'final_info.json' was produced. Please check the code to ensure it saves results correctly."
            # --- This is still a failure in practice, so return 1
            return 1, next_prompt, traceback, message

        return result.returncode, next_prompt, traceback, message

    except TimeoutExpired:
        print(f"Run {run_num} timed out after {timeout} seconds")
        if osp.exists(osp.join(cwd, f"run_{run_num}")):
            shutil.rmtree(osp.join(cwd, f"run_{run_num}"))
        next_prompt = f"Run timed out after {timeout} seconds"
        return 1, next_prompt, None, None


# PERFORM EXPERIMENTS
# --- MODIFIED: Added job_id ---
def perform_experiments(idea, folder_name, coder, baseline_results, job_id) -> bool:
    ## RUN EXPERIMENT
    current_iter = 0
    run = 1
    next_prompt = coder_prompt.format(
        title=idea["Title"],
        method=idea.get("Method", "N/A"),
        idea=idea["Experiment"],
        max_runs=MAX_RUNS,
        baseline_results=baseline_results,
    )
    while run < MAX_RUNS + 1:
        if current_iter >= MAX_ITERS:
            print("Max iterations reached")
            break
        coder_out = coder.run(next_prompt)
        print(coder_out)
        if "litellm.BadRequestError" in coder_out:
            return False
        if "ALL_COMPLETED" in coder_out:
            break

        baseline_script_path = os.path.join(folder_name, 'run_0', 'experiment.py')
        new_script_path = os.path.join(folder_name, 'experiment.py')

        if not osp.exists(baseline_script_path):
            print(f"[WARNING] Baseline file {baseline_script_path} not found. Skipping file comparison.")
        elif filecmp.cmp(new_script_path, baseline_script_path):
            print("AI Coder did not modify the code. Re-prompting.")
            next_prompt = "You did not modify the code. Please apply the changes as requested."
            current_iter += 1
            continue

        # --- MODIFIED: Pass job_id and idea to run_experiment ---
        return_code, next_prompt, traceback, message = run_experiment(folder_name, run, job_id, idea)
        # --- END MODIFICATION ---

        if traceback:
            functions_codes = ""
            for t in traceback:
                functions_codes = functions_codes + f"line: {t[1]}, function: {t[2]}, codes: {t[3]} \n"
            code_structure = coder.run(
                code_structure_prompt_v2.format(error_messages=next_prompt, function_code=functions_codes))
            next_prompt = debug_prompt_with_structure_v2.format(error_messages=next_prompt,
                                                                code_structure=code_structure)

        if return_code == 0:
            run += 1
            current_iter = 0
        current_iter += 1
    if current_iter >= MAX_ITERS:
        print("Not all experiments completed.")
        return False
    return True