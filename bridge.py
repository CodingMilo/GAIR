import sys
import os
import pandas as pd
import json
from pathlib import Path
from datetime import datetime
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
    # Save in a subfolder "dashboard_runs" within experiments to keep it tidy
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
        'enable_parallel': n_runs > 1,
        'max_workers': max_workers,
        'rate_limit_seconds': 1.0,
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
        # Simplified hard question filtering (can be improved)
        df = df.head(10) 

    # Run!
    # Note: We wrap the runner to provide progress updates to the dashboard
    class DashboardLogger(BenchmarkLogger):
        def log_run_results(self, run_idx, results):
            log_file = super().log_run_results(run_idx, results)
            if progress_callback:
                for i, res in enumerate(results):
                    progress_callback({
                        "type": "update",
                        "completed": i + 1,
                        "total": len(results),
                        "last_log": {
                            "question_id": res["question_id"],
                            "prediction": res["extracted_answer"],
                            "is_correct": "N/A"
                        }
                    })
            return log_file

    dash_logger = DashboardLogger(str(results_path), config)

    
    # Execute
    results_df = runner.run_benchmark(
        dataset_df=df,
        num_repetitions=n_runs,
        logger=dash_logger,
        enable_parallel=config['enable_parallel'],
        max_workers=max_workers
    )

    return results_df
