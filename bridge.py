import sys
import os
import pandas as pd
import json
import time
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from supporting_scripts import OpenRouterClient, BenchmarkRunner, BenchmarkLogger

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
        'enable_parallel': True, # We force parallel for speed
        'max_workers': max_workers,
        'rate_limit_seconds': 0.5, # Faster rate for parallel
        'rag_tex_path': str(scripts_dir / "rag.tex") if use_rag else None,
        'system_prompt': custom_system_prompt
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
        # Example hard questions filtering - keep only problematic ones if you have a list
        # For now, let's just take a sample to demonstrate
        df = df.sample(min(15, len(df))) 

    # --- TRUE PARALLEL EXECUTION ---
    all_runs_results = {}
    completed_count = 0
    total_total = len(df) * n_runs

    # Ground truth for live accuracy
    ground_truth = {}
    if mode == "train":
        ground_truth = dict(zip(df['question_id'], df['answer']))

    def process_run(run_idx):
        results = []
        # Parallelize QUESTIONS within the run for maximum speed
        with ThreadPoolExecutor(max_workers=max_workers) as q_executor:
            q_futures = {
                q_executor.submit(runner.run_single_question, row['question'], row['question_id']): row 
                for _, row in df.iterrows()
            }
            
            for q_future in as_completed(q_futures):
                res = q_future.result()
                
                # Live feedback
                nonlocal completed_count
                completed_count += 1
                
                if progress_callback:
                    is_correct = "N/A"
                    if mode == "train":
                        correct_ans = ground_truth.get(res['question_id'])
                        is_correct = str(res['extracted_answer']).strip().lower() == str(correct_ans).strip().lower()

                    progress_callback({
                        "type": "update",
                        "completed": completed_count,
                        "total": total_total,
                        "last_log": {
                            "run": run_idx,
                            "question_id": res["question_id"],
                            "prediction": res["extracted_answer"],
                            "is_correct": is_correct,
                            "cost": res.get("usage", {}).get("cost", 0)
                        }
                    })
                results.append(res)
        
        # Sort by question_id to maintain order for logging
        results.sort(key=lambda x: x['question_id'])
        logger.log_run_results(run_idx, results)
        return run_idx, results

    # Run repetitions in parallel
    with ThreadPoolExecutor(max_workers=min(n_runs, 5)) as run_executor:
        run_futures = [run_executor.submit(process_run, r) for r in range(1, n_runs + 1)]
        for f in as_completed(run_futures):
            r_idx, r_res = f.result()
            all_runs_results[r_idx] = r_res

    # Final reports (mimic engine behavior for dashboard archives)
    # We need a dataframe for the logger
    final_df = pd.DataFrame()
    final_df['question_id'] = df['question_id'].values
    for r_idx, r_res in all_runs_results.items():
        # Sort to match order
        r_res.sort(key=lambda x: x['question_id'])
        final_df[f"prediction_{r_idx}"] = [x['extracted_answer'] for x in r_res]

    if mode == "train":
        correct_df = pd.read_csv(solution_path)
        usage_summary = client.get_usage_summary()
        logger.generate_result_report(final_df, correct_df, usage_summary, n_runs)
        logger.generate_wrong_answers_report(final_df, correct_df, df)
    
    # Save solution.csv
    solution_cols = ['question_id'] + [f'prediction_{i}' for i in range(1, n_runs+1)]
    final_df[solution_cols].to_csv(results_path / "solution.csv", index=False)

    return final_df

