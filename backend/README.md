# InternAgent: When Agent Becomes the Scientist – Building Closed-Loop System from Hypothesis to Verification

[[ Paper 📓 ]](https://arxiv.org/abs/2505.16938) [[ Apply Page 💡 ]](https://discovery.intern-ai.org.cn) [[ Website 🏠 ]](https://alpha-innovator.github.io/InternAgent-project-page)

<i>
From One Idea to Autonomous Experimentation
</i>
</div>

## 🔥 News
  - <p style='text-align:justify'><i>2025.09.29</i>: &nbsp; 🔥 Our <b>deep research agent, InternAgent-DR</b>, demonstrates strong competitiveness across the GAIA, HLE, GPQA, and TRQA benchmarks, achieving state-of-the-art results on multiple tasks.
  - <p style='text-align:justify'><i>2025.09.12</i>: &nbsp; 🔥 Our latest <b>coding agent InternAgent-MLE</b> has achieved the championship in MLE-bench with <b>36.44%</b> medal rate, ranking <b>#1</b> among all competing methods, see details at <a href="https://github.com/openai/mle-bench">openai/mle-bench</a>. 
  - <p style='text-align:justify'><i>2025.08.06</i>: &nbsp; 🔥 InternAgent now supports Intern-S1 which combines strong general-task capabilities with state-of-the-art performance on a wide range of scientific tasks. Check <a href="https://internlm.intern-ai.org.cn/api/document">here</a> for how to use Intern-S1.
  - <p style='text-align:justify'><i>2025.07.17</i>: &nbsp; 🔥 The source code of InternAgent has been partially open-sourced. The complete version of InternAgent (covering 12 types of tasks for autonomous scientific research) will be open-sourced soon. This code repository can be used for full-cycle autonomous scientific research, ranging from hypothesis generation to automated experimental execution. It includes the source code for our initial version, covering paper retrieval, idea generation, coding, and experimental execution.
  - <p style='text-align:justify'><i>2025.07.10</i>: &nbsp; NovelSeek has be renamed to <b>InternAgent</b>. This change embodies our hopeful vision for autonomous scientific research framework, and we hope it will empower all researchers to achieve great scientific discoveries.</p>


## 📖 Overview

![InternAgent](/images/internagent_overall.png)

InternAgent can support **12** types of scientific research tasks ranging from the AI field to the science field, including reaction yield prediction, molecular dynamics, power flow estimation, time series forecasting, transcription prediction, enhancer activity prediction, sentiment classification, 2D image classification, 3D point classification, 2D semantic segmentation, 3D autonomous driving, large vision-language model fine-tuning.

## 🌟 Core Features

![Framework](/images/internagent_framework.png)

InternAgent covers three main capabilities: (1) **Self-evolving idea generation with human-interactive feedback**, (2) **Idea-to-methodology construction**, and (3) **Evolutionary experimental planning and execution**. 

It is a unified, closed-loop multi-agent system designed to automate and accelerate innovative research across scientific domains. Through intelligent agent collaboration, our system enables **end-to-end automation** from idea generation and methodology construction to experimental execution, dramatically enhancing research efficiency and creativity.

### 💡 Self-Evolving Idea Generation with Human-Interactive Feedback
- Autonomous generation, selection, and evolution of innovative research ideas through multi-agent collaboration
- Supports interactive human feedback, enabling continuous refinement of ideas with expert insights
- Dynamically integrates literature, code, and domain knowledge to inspire diverse innovation pathways

### 🏗️ Idea-to-Methodology Construction
- Systematically transforms creative ideas into actionable and verifiable research methodologies
- Integrates baseline code, literature, and expert knowledge to automatically generate comprehensive methodological frameworks
- Supports iterative refinement and traceability of research methods

### 🛠️ Evolutionary Experimental Planning and Execution
- Automates complex experimental workflow planning, code implementation, and debugging
- Employs exception-guided intelligent debugging to automatically identify and resolve code issues
- Enables adaptive evolution and continuous optimization of experimental plans

### 🤖 Multi-Agent Orchestration
- Coordinates specialized agents such as Survey, Coding, Idea Innovation, and Assessment Agents and so on 
- Manages data flow, task scheduling, and human interaction points for efficient and coherent research processes
- Supports extensibility and compatibility with diverse scientific tasks

---

**InternAgent** delivers an "end-to-end algorithmic innovation", empowering AI+X researchers to rapidly complete the full research loop—from idea to methodology to experimental validation—accelerating scientific discovery and breakthroughs.

## 🔬 Supported Research Tasks

- Suzuki Yield Prediction
- Molecular Dynamics Simulation
- Enhancer Activity Prediction
- Transcription Prediction for Perturbation Response
- Power Flow Estimation
- Time Series Forecasting
- Semantic Segmentation
- Image Classification
- Sentiment Analysis
- Point Cloud Classification
- Autonomous Driving
- VLM & LLM Fine-tuning
- ......

## 🎉 Benchmark Results

### Results on 12 different types of research tasks

The results report both maximum performance and mean performance (i.e., the average across runs with performance gains) achieved by InternAgent and Dolphin. InternAgent consistently improves upon the baseline and outperforms Dolphin across all tasks, spanning AI and scientific task domains.

#### Max Performance (per task)

| Task | Metric | Baseline | Dolphin | InternAgent |
|---|---|---:|---:|---:|
| AutoRYP | R^2 ↑ | 27.6 | 31.8 (+4.2) | **35.4 (+7.8)** |
| AutoMD | Forces-MAE ↓ | 0.158 | 0.152 | **0.148** |
| AutoPower | RMSE ↓ | 0.00473 | 0.00455 | **0.00426** |
| AutoTSF | MAE ↓ | 0.4382 | 0.4627 | **0.4331** |
| AutoTPPR | MSE ↓ | 0.197 | 0.173 | **0.146** |
| AutoEAP | HK-PCC ↑ | 0.65 | 0.76 | **0.79** |
| AutoSenCls | Acc ↑ | 91.0 | 92.5 (+1.5) | **93.5 (+2.5)** |
| Auto2DCls | Top-1 Acc ↑ | 81.2 | 82.0 (+0.8) | **83.3 (+2.1)** |
| Auto3DCls | OA ↑ | 91.0 | 93.9 (+2.9) | **95.5 (+4.5)** |
| Auto2DSeg | mIoU ↑ | 78.8 | - | **81.0 (+2.2)** |
| AutoPCDet | mAP ↑ | 65.0 | - | **65.9 (+0.9)** |
| AutoVLM | QA ↑ | 67.1 | - | **67.6 (+0.5)** |

#### Average Performance (per task)

| Task | Metric | Baseline | Dolphin | InternAgent |
|---|---|---:|---:|---:|
| AutoRYP | R^2 ↑ | 27.6 | 31.3 (+3.7) | **33.5 (+5.9)** |
| AutoMD | Forces-MAE ↓ | 0.158 | 0.155 | **0.152** |
| AutoPower | RMSE ↓ | 0.00473 | 0.00459 | **0.00447** |
| AutoTSF | MAE ↓ | 0.4382 | - | **0.4346** |
| AutoTPPR | MSE ↓ | 0.197 | 0.179 | **0.170** |
| AutoEAP | HK-PCC ↑ | 0.65 | 0.73 | **0.77** |
| AutoSenCls | Acc ↑ | 91.0 | 91.8 (+0.8) | **92.5 (+1.5)** |
| Auto2DCls | Top-1 Acc ↑ | 81.2 | 81.8 (+0.6) | **82.2 (+1.0)** |
| Auto3DCls | OA ↑ | 91.0 | 92.0 (+1.0) | **93.4 (+2.4)** |
| Auto2DSeg | mIoU ↑ | 78.8 | - | **80.1 (+1.3)** |
| AutoPCDet | mAP ↑ | 65.0 | - | **65.7 (+0.7)** |
| AutoVLM | QA ↑ | 67.1 | - | **67.6 (+0.5)** |


### 👨‍💻  MLE-Bench: Record-Breaking Performance in Just 12 Hours!

InternAgent-MLE has achieved **36.44%** medal rate on the MLE-Bench, securing the **#1** position among all competing methods - and remarkably, this was accomplished in **only 12 hours** of running time!

| Agent | Low == Lite (%) | Medium (%) | High (%) | All (%) | Running Time (hours) | Date |
|---------|--------|-----------|---------|----------|--------|------
| [InternAgent-MLE](https://github.com/Alpha-Innovator/InternAgent/) deepseek-r1 | 62.12 ± 3.03 | 26.32 ± 2.63 | 24.44 ± 2.22| **36.44 ± 1.18** | **12** | 2025-09-12	
| Neo multi-agent | 48.48 ± 1.52 | 29.82 ± 2.32	| 24.44 ± 2.22 | 34.22 ± 0.89 | 36 | 2025-07-28 
| R&D-Agent o3 + GPT-4.1 | 51.52 ± 6.9 | 19.3 ± 5.5 | 26.67 ± 0 | 30.22 ± 1.5 | 24 | 2025-08-15 
| ML-Master deepseek-r1 | 48.5 ± 1.5 | 20.2 ± 2.3 | 24.4 ± 2.2| 29.3 ± 0.8 | 12 | 2025-06-17 
| R&D-Agent o1-preview | 48.18 ± 2.49 | 8.95 ± 2.36 | 18.67 ± 2.98 | 22.4 ± 1.1 | 24 | 2025-05-14 
| AIDE o1-preview | 34.3 ± 2.4 | 8.8 ± 1.1 | 10.0 ± 1.9 | 16.9 ± 1.1 | 24 | 2024-10-08 
| AIDE gpt-4o-2024-08-06 | 19.0 ± 1.3 | 3.2 ± 0.5 | 5.6 ± 1.0 | 8.6 ± 0.5 | 24 | 2024-10-08 
| AIDE claude-3-5-sonnet-20240620 | 19.4 ± 4.9 | 2.6 ± 1.5 | 2.3 ± 2.3 | 7.5 ± 1.8 | 24 | 2024-10-08 
| OpenHands gpt-4o-2024-08-06 | 11.5 ± 3.4 | 2.2 ± 1.3 | 1.9 ± 1.9 | 5.1 ± 1.3 | 24 | 2024-10-08 
| AIDE llama-3.1-405b-instruct | 8.3 ± 2.6 | 1.2 ± 0.8 | 0.0 ± 0.0 | 3.1 ± 0.9 | 24 | 2024-10-08 
| MLAB gpt-4o-2024-08-06 | 4.2 ± 1.5 | 0.0 ± 0.0 | 0.0 ± 0.0 | 1.3 ± 0.5 |  24 | 2024-10-08 

### 🧪  GAIA, GPQA-diamond and HLE benchmarks  
We benchmark InternAgent-DR on a series of benchmarks, including GAIA, HLE and GPQA, and achieved SOTA results.

| Model/Framework | GAIA Avg | GPQA Avg | HLE text only | HLE All |
|-----------------|----------|----------|---------------|---------|
| Intern-S1 | 15.15 | 78.26 | 8.90 | 8.30 |
| Deepseek-R1 | 18.78 | 82.32 | 8.60 | - |
| o4-mini | 16.97 | 78.28 | 14.50 | 14.28 |
| GPT-5 | - | _85.35_ | 25.85 | 24.76 |
| OpenAI DR | 67.36 | - | - | 26.60 |
| Manus | 73.30 | - | - | - |
| Gemini Deep Research | - | - | - | 26.90 |
| MiroFlow | _74.50_ | - | 29.50 | 27.20 |
| OWL | 69.70 | - | - | - |
| X-Masters | - | - | **32.10** | _27.72_ |
| InternAgent-DR (Qwen-235B) | 58.79 | 66.16 | 15.04 | 14.84 |
| InternAgent-DR (o4-mini) | **76.96** | **87.37** | _31.60_ | **30.80** |




## 🚀 How to use the early version, Dolphin?

### Installation

```
conda create -n dolphin python=3.11
conda activate dolphin

# Install PyPI requirements
pip install -r requirements.txt
```

### Start Auto-Research using Dolphin

```shell
bash launch_dolphin.sh

# modify launch_dolphin.py line # line 189 if round > 0
# exp_base_file_list = [List your exp dir] 
```

- Note that you need to add api_key and specify the model and topic in `launch_dolphin.sh`. You can refer to the [doc](./docs/ollama_doc.md) if you want to use self-deployed model.
- Data for Point Classfication, Image Classification, and Sentiment Classification tasks can be downloaded [here](https://drive.google.com/drive/folders/1mq1y7EWW9dgPlS26hXNa3wxL7_2vvNju?usp=sharing).

## 🧭 AutoAD Backend API (FastAPI)

The `backend/server` package exposes a lightweight FastAPI layer that lets you scaffold new experiments and drive the agentic AutoAD pipeline directly from your chat-style frontend.

### Run the API server

1. Install dependencies (the main `requirements.txt` already includes FastAPI, Uvicorn, and aider):

   ```bash
   pip install -r requirements.txt
   ```

2. Launch the development server from the backend root:

   ```bash
   uvicorn app.main:app --reload --app-dir server
   ```

   The service will be available at `http://localhost:8000` by default, with the interactive docs at `/docs`.

  > **Tip:** To persist session history across restarts, ensure a MongoDB instance is reachable and set the following environment variables (defaults target a local daemon):
  >
  > ```bash
  > export MONGODB_URI="mongodb://127.0.0.1:27017"
  > export MONGODB_DB="autoad"
  > export MONGODB_SESSION_COLLECTION="sessions"
  > ```
  >
  > The FastAPI app automatically loads `.env`, so adding these keys there works too.

### Session persistence and monitoring

- Session metadata is now mirrored into MongoDB; history survives uvicorn reloads and server restarts. If MongoDB is unavailable, the service gracefully falls back to in-memory tracking.
- A lightweight dashboard (`session_monitor.html`) lives at the backend root. Serve it with `python -m http.server 5500` and open `http://127.0.0.1:5500/session_monitor.html` to watch session progress and final artifact paths.

### Project management endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/projects` | Create a new experiment scaffold (directories, baseline files, prompts). |
| `GET` | `/projects` | List all provisioned projects with their RAG state and timestamps. |
| `GET` | `/projects/{slug}` | Fetch the full configuration for a specific project. |

**Create project request body (`ProjectCreateRequest`)**

```json
{
  "name": "Protein Folding Explorer",
  "topic": "Protein folding pathways",
  "objective": "Design improved folding prediction algorithms",
  "success_metric": "Top-1 accuracy on CASP",
  "user_persona": "Computational biologist",
  "data_sources": ["CASP15", "AlphaFold DB"],
  "constraints": ["<24h runtime", "NVIDIA A100"],
  "preferred_modalities": ["transformers", "graph neural networks"],
  "enable_rag": true,
  "seed": 2025,
  "rag_max_papers": 20,
  "rag_memory_papers": 10,
  "notes": "Prioritize explainability."
}
```

The response contains the slug, filesystem paths, and timestamps so you can immediately trigger AutoAD runs.

### Session orchestration endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/sessions` | Kick off the AutoAD pipeline for a project (idea generation → experiments). |
| `GET` | `/sessions` | Retrieve a summary list of all sessions for dashboard views. |
| `GET` | `/sessions/{session_id}` | Fetch the full status snapshot including the latest stage, events, and result folders. |
| `GET` | `/sessions/{session_id}/events` | Poll just the event timeline for streaming-style UIs. |

**Launch session request body (`SessionCreateRequest`)**

```json
{
  "project_slug": "protein-folding-explorer",
  "model": "gemini-2.5-flash-lite",
  "code_model": "flash",
  "parallel": 0,
  "num_ideas": 12,
  "skip_idea_generation": false,
  "skip_novelty_check": false,
  "check_similarity": true,
  "embedding_model": "sentence-transformers/all-roberta-large-v1",
  "use_rag": true,
  "topic_override": "Protein folding stability",
  "round": 0
}
```

The service enqueues the job, returns a `session_id`, and emits stage-by-stage events (Queued → Preparing → Retrieval → Idea Generation → Novelty Check → Execution → Complete/Failed). The `result_paths` array lists the directories under `results/<slug>/` that successfully compiled and ran.

## Citation
```
@article{team2025novelseek,
  title={NovelSeek: When Agent Becomes the Scientist--Building Closed-Loop System from Hypothesis to Verification},
  author={Team, NovelSeek and Zhang, Bo and Feng, Shiyang and Yan, Xiangchao and Yuan, Jiakang and Yu, Zhiyin and He, Xiaohan and Huang, Songtao and Hou, Shaowei and Nie, Zheng and others},
  journal={arXiv preprint arXiv:2505.16938},
  year={2025}
}
```
