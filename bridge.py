import sys
import os
import pandas as pd
import json
import time
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from supporting_scripts import OpenRouterClient, BenchmarkRunner, BenchmarkLogger

def get_hard_question_ids():
    """Identifies 'hard' questions based on previous failures of the Trinity model in the original GAIR repo."""
    # We look into the original GAIR/outputs directory
    base_dir = Path(__file__).parent.parent
    outputs_path = base_dir / "GAIR" / "outputs"
    
    if not outputs_path.exists():
        print(f"[WARN] Original outputs path {outputs_path} not found.")
        return []

    trinity_runs = list(outputs_path.glob("arcee-ai_trinity-large_preview_free_*"))
    
    if not trinity_runs:
        print("[WARN] No Trinity logs found. Using all questions.")
        return []
        
    # Take the most recent run
    latest_run = max(trinity_runs, key=lambda p: p.stat().st_mtime)
    results_file = latest_run / "df_results.csv"
    
    if not results_file.exists():
        print(f"[WARN] File {results_file} missing.")
        return []
        
    df_trinity = pd.read_csv(results_file)
    
    # Exclude the summary row (last one)
    if len(df_trinity) > 0:
        df_trinity = df_trinity.iloc[:-1]
        
    # Identify indices where Trinity failed (mean accuracy == 0)
    # The index in the CSV corresponds to (question_id - 1)
    hard_indices = df_trinity[df_trinity["mean"] == 0.0].index.tolist()
    hard_ids = [idx + 1 for idx in hard_indices]
    
    print(f"[INFO] {len(hard_ids)} hard questions identified via Trinity logs.")
    return hard_ids

import pandas as pd
import json
import time
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from supporting_scripts import OpenRouterClient, BenchmarkRunner, BenchmarkLogger

def get_hard_question_ids():
    """Identifies 'hard' questions based on previous failures of the Trinity model in the original GAIR repo."""
    # We look into the original GAIR/outputs directory
    base_dir = Path(__file__).parent.parent
    outputs_path = base_dir / "GAIR" / "outputs"
    
    if not outputs_path.exists():
        print(f"[WARN] Original outputs path {outputs_path} not found.")
        return []

    trinity_runs = list(outputs_path.glob("arcee-ai_trinity-large_preview_free_*"))
    
    if not trinity_runs:
        print("[WARN] No Trinity logs found. Using all questions.")
        return []
        
    # Take the most recent run
    latest_run = max(trinity_runs, key=lambda p: p.stat().st_mtime)
    results_file = latest_run / "df_results.csv"
    
    if not results_file.exists():
        print(f"[WARN] File {results_file} missing.")
        return []
        
    df_trinity = pd.read_csv(results_file)
    
    # Exclude the summary row (last one)
    if len(df_trinity) > 0:
        df_trinity = df_trinity.iloc[:-1]
        
    # Identify indices where Trinity failed (mean accuracy == 0)
    # The index in the CSV corresponds to (question_id - 1)
    hard_indices = df_trinity[df_trinity["mean"] == 0.0].index.tolist()
    hard_ids = [idx + 1 for idx in hard_indices]
    
    print(f"[INFO] {len(hard_ids)} hard questions identified via Trinity logs.")
    return hard_ids

def run_experiment(
    mode="train", 
    n_runs=1, 
    use_rag=True, 
    hard_only=False,
    model_name="openai/gpt-4o-mini",
    prompt_name="default",
    custom_system_prompt=None,
    temperature=1.0,
    rag_k=2,
    max_workers=5,
    progress_callback=None
):
    # Setup paths
    base_dir = Path(__file__).parent
    scripts_dir = base_dir / "scripts"
    dataset_path = base_dir / "data" / ("train.csv" if mode == "train" else "test.csv")
    solution_path = base_dir / "data" / ("train.csv" if mode == "train" else "sample_submission.csv")
    
    # Create experiments folder
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_safe = model_name.replace("/", "-")
    results_path = base_dir / "experiments" / "dashboard_runs" / f"{model_safe}_{timestamp}"
    results_path.mkdir(parents=True, exist_ok=True)

    # Config for BenchmarkRunner
    config = {
        'model': model_name,
        'llm_script': str(scripts_dir / "my_eval.py"),
        'temperature': temperature,
        'max_tokens': 4096,
        'max_reasoning_tokens': None,
        'num_repetitions': n_runs,
        'dataset_path': str(dataset_path),
        'solution_path': str(solution_path),
        'testing_mode': mode == "test",
        'enable_parallel': True, 
        'max_workers': max_workers,
        'rate_limit_seconds': 0.5,
        'rag_tex_path': str(scripts_dir / "rag.tex") if use_rag else None,
        'system_prompt': custom_system_prompt,
        'embedding_model': "text-embedding-3-small" # Default embedding model
    }

    # Save config to folder
    with open(results_path / "config.json", "w") as f:
        json.dump(config, f, indent=2)

    # Initialize components
    client = OpenRouterClient()
    runner = BenchmarkRunner(client, str(results_path), config)
    logger = BenchmarkLogger(str(results_path), config)

    # Load data
    df = pd.read_csv(dataset_path)
    if hard_only and mode == "train":
        hard_ids = get_hard_question_ids()
        if hard_ids:
            if "question_id" in df.columns:
                df = df[df["question_id"].isin(hard_ids)].copy()
            else:
                df = df.iloc[[idx for idx in range(len(df)) if (idx + 1) in hard_ids]].copy()
            print(f"[FILTER] Restricted to {len(df)} hard questions.")

    # --- TRUE PARALLEL EXECUTION WITH MAIN THREAD LOOP ---
    all_runs_results = {i+1: [] for i in range(n_runs)}
    completed_count = 0
    total_total = len(df) * n_runs

    ground_truth = {}
    if mode == "train":
        ground_truth = dict(zip(df['question_id'], df['answer']))

    # Prepare flat list of tasks (Run ID, Question String, Question ID Integer)
    tasks = []
    for run_i in range(1, n_runs + 1):
        for index, row_series in df.iterrows():
            question_text = str(row_series['question'])
            question_id_val = int(row_series['question_id'])
            tasks.append({
                "run_id": run_i,
                "question_text": question_text,
                "question_id": question_id_val
            })

    # Helper function for processing a single task
    def process_task_wrapper(task_info, runner_ref, mode_ref, ground_truth_ref):
        r_id = task_info["run_id"]
        q_text = task_info["question_text"]
        q_id = task_info["question_id"]
        
        # execution
        result = runner_ref.run_single_question(q_text, q_id)
        
        # correctness check
        is_corr = "N/A"
        if mode_ref == "train":
            correct_ans = ground_truth_ref.get(q_id)
            is_corr = str(result['extracted_answer']).strip().lower() == str(correct_ans).strip().lower()
            
        return r_id, result, is_corr

    # Single executor for all tasks to maximize parallelism
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        futures = []
        for task in tasks:
            f = executor.submit(process_task_wrapper, task, runner, mode, ground_truth)
            futures.append(f)
        
        for future in as_completed(futures):
            try:
                run_i, res, is_correct = future.result()
                
                all_runs_results[run_i].append(res)
                completed_count += 1
                
                if progress_callback:
                    progress_callback({
                        "type": "update",
                        "completed": completed_count,
                        "total": total_total,
                        "last_log": {
                            "run": run_i,
                            "question_id": res["question_id"],
                            "prediction": res['extracted_answer'], 
                            "is_correct": is_correct,
                            "cost": res.get("usage", {}).get("cost", 0)
                        }
                    })
            except Exception as e:
                print(f"Error in worker: {e}")

    # Sort and Log results per run
    final_df = pd.DataFrame()
    final_df['question_id'] = df['question_id'].values


    for r_idx in range(1, n_runs + 1):
        r_res = all_runs_results[r_idx]
        r_res.sort(key=lambda x: x['question_id'])
        logger.log_run_results(r_idx, r_res)
        final_df[f"prediction_{r_idx}"] = [x['extracted_answer'] for x in r_res]

    # Force report generation
    correct_df = pd.read_csv(solution_path)
    usage_summary = client.get_usage_summary()
    logger.generate_result_report(final_df, correct_df, usage_summary, n_runs)
    logger.generate_wrong_answers_report(final_df, correct_df, df)
    
    # Save solution.csv
    solution_cols = ['question_id'] + [f'prediction_{i}' for i in range(1, n_runs+1)]
    final_df[solution_cols].to_csv(results_path / "solution.csv", index=False)

    return final_df



