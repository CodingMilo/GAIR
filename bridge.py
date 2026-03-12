import sys
import os
import pandas as pd
import json
import time
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter, defaultdict
from supporting_scripts import OpenRouterClient, BenchmarkRunner, BenchmarkLogger

def get_hard_question_ids():
    """Returns the hard-coded list of question IDs that were difficult for Trinity model."""
    # IDs corresponding to questions with 0.0 accuracy in the reference run (Trinity)
    hard_ids = [7, 9, 10, 11, 16, 17, 19, 24, 25, 26, 29, 34, 35, 39, 45, 47]
    print(f"[INFO] Using {len(hard_ids)} hard-coded difficult questions.")
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
    rag_k=8,
    max_workers=5,
    max_tokens=512,
    rate_limit_seconds=0.3,
    use_fewshot=False,
    fewshot_k=3,
    use_self_critique=False,
    use_tool_calling=False,
    use_json_format=False,
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
        'max_tokens': max_tokens,
        'max_reasoning_tokens': None,
        'num_repetitions': n_runs,
        'dataset_path': str(dataset_path),
        'solution_path': str(solution_path),
        'testing_mode': mode == "test",
        'enable_parallel': True, 
        'max_workers': max_workers,
        'rate_limit_seconds': rate_limit_seconds,
        'rag_tex_path': str(scripts_dir / "rag.tex") if use_rag else None,
        'rag_k': rag_k,
        'system_prompt': custom_system_prompt,
        'embedding_model': "openai/text-embedding-3-small",
        'use_fewshot': use_fewshot,
        'fewshot_k': fewshot_k,
        'use_self_critique': use_self_critique,
        'use_tool_calling': use_tool_calling,
        'use_json_format': use_json_format,
        'train_path': str(base_dir / "data" / "train.csv"),
    }

    # Save config to folder
    with open(results_path / "config.json", "w") as f:
        json.dump(config, f, indent=2)

    # Configure global rate limiter BEFORE creating the client.
    # The config's rate_limit_seconds must be applied here; otherwise the
    # GlobalRateLimiter singleton uses its default (1.0 s), ignoring our setting.
    from supporting_scripts.openrouter_client import GlobalRateLimiter
    GlobalRateLimiter.reset()
    GlobalRateLimiter.get_instance(min_interval=config['rate_limit_seconds'])

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
                # Fallback if question_id is not explicitly in columns but rows are indexed 0..N
                # Assuming index+1 is question_id is risky if df is already shuffled/filtered, 
                # but standard train.csv usually has question_id.
                # If question_id column exists, isin works.
                # If not, we assume line number mapping.
                pass 
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

    # Generate reports and save CSVs
    usage_summary = client.get_usage_summary()
    testing_mode = (mode == "test")

    if testing_mode:
        # In test mode there are no ground truth answers — skip accuracy reports
        logger.generate_result_report(final_df, None, usage_summary, n_runs, testing_mode=True)
    else:
        correct_df = pd.read_csv(solution_path)
        logger.generate_result_report(final_df, correct_df, usage_summary, n_runs, testing_mode=False)
        logger.generate_wrong_answers_report(final_df, correct_df, df)

    # Save solution.csv (predictions only)
    solution_cols = ['question_id'] + [f'prediction_{i}' for i in range(1, n_runs+1)]
    final_df[solution_cols].to_csv(results_path / "solution.csv", index=False)

    # In test mode, also generate the Kaggle submission CSV.
    # "Average cost per run" column: each row holds the average cost for THAT
    # question across all n_runs (= sum of all API calls for that question in
    # every run, divided by n_runs). This includes the first call, any truncation-
    # recovery calls, and the self-critique call when enabled — because my_eval.py
    # accumulates all of them into the per-question usage dict before returning.
    # The Kaggle evaluator takes the column mean, so the final metric equals the
    # grand mean cost per question.
    if testing_mode:
        # --- Per-question average cost ---
        q_costs: dict = defaultdict(list)
        for r_idx in range(1, n_runs + 1):
            for res in all_runs_results[r_idx]:
                q_costs[int(res['question_id'])].append(
                    float((res.get('usage') or {}).get('cost', 0.0) or 0.0)
                )
        per_q_avg_cost = {
            qid: sum(costs) / len(costs)
            for qid, costs in q_costs.items()
        }

        kaggle_df = final_df[solution_cols].copy()

        # --- Fill null/empty predictions to prevent Kaggle rejection ---
        # If a question couldn't be parsed, use the most common answer for that
        # question across the other runs. Absolute fallback: "a".
        pred_cols_list = [f"prediction_{i}" for i in range(1, n_runs + 1)]
        for col in pred_cols_list:
            kaggle_df[col] = kaggle_df[col].replace("", None)
        for idx in kaggle_df.index:
            row_preds = [kaggle_df.at[idx, col] for col in pred_cols_list]
            non_null = [v for v in row_preds if v is not None and str(v).strip() != ""]
            if len(non_null) < len(pred_cols_list):
                fallback = Counter(non_null).most_common(1)[0][0] if non_null else "a"
                for col in pred_cols_list:
                    val = kaggle_df.at[idx, col]
                    if val is None or str(val).strip() == "":
                        kaggle_df.at[idx, col] = fallback

        # Set per-question average cost
        kaggle_df['Average cost per run'] = (
            kaggle_df['question_id'].map(per_q_avg_cost).fillna(0.0)
        )

        kaggle_path = results_path / "kaggle_submission.csv"
        kaggle_df.to_csv(kaggle_path, index=False)
        overall_avg = kaggle_df['Average cost per run'].mean()
        print(f"[INFO] Kaggle submission saved: {kaggle_path}")
        print(f"[INFO] Avg cost per question: ${overall_avg:.6f}  |  ×75 equiv: ${overall_avg * 75:.6f}")

    return final_df
