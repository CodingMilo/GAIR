#!/usr/bin/env python3
"""
Batch test multiple LLM models with parallel execution.

Configuration:
    - Option 1: Edit CONFIG_PATH variable below to point to your JSON config file
    - Option 2: Use CLI: python batch_test_models.py --config path/to/config.json

Usage:
    python batch_test_models.py
    python batch_test_models.py --config my_config.json
"""
import shutil
import json
import sys
import os
import argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import List, Dict
import time

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from supporting_scripts import OpenRouterClient, BenchmarkRunner, BenchmarkLogger
import pandas as pd
from tqdm import tqdm

# Import summary generation functions from create_summary_report
from supporting_scripts import create_summary_report as summary_gen
from supporting_scripts.create_summary_report import create_solution_kaggle_csv

# Import Kaggle scoring function
def _get_calculate_kaggle_score():
    """Lazy import of calculate_kaggle_score."""
    import importlib.util
    from pathlib import Path as PathImport
    # __file__ is in devel/scripts/, we need devel/supporting_scripts/test_eval_code/eval_code.py
    _eval_code_file = PathImport(__file__).parent.parent / 'supporting_scripts' / 'test_eval_code' / 'eval_code.py'
    
    spec = importlib.util.spec_from_file_location("eval_code", _eval_code_file)
    module = importlib.util.module_from_spec(spec)
    import sys as sys_module
    sys_module.modules["eval_code"] = module
    spec.loader.exec_module(module)
    
    return module.calculate_kaggle_score


# ============================================================================
# CONFIGURATION
# ============================================================================

# Default config path (can be overridden with --config CLI argument)
# Set this to your preferred config file, or use CLI
CONFIG_PATH = './configs/training_data_zero_shot.json'


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def load_config(config_path: str) -> dict:
    """Load configuration from JSON file."""
    config_file = Path(config_path)
    
    # If relative path, resolve relative to script directory
    if not config_file.is_absolute():
        script_dir = Path(__file__).parent
        config_file = script_dir / config_file
    
    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_file}")
    
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    return config


def parse_path_settings(config: dict) -> dict:
    """ Transform relative paths into absolute paths. """
    try:
        results_path = Path(config.get('results_path', ''))
        data_setpath = Path(config.get('dataset_path', ''))
        solution_path = Path(config.get('solution_path', ''))
        eval_script_path = Path(config.get('eval_script_path', ''))
    except ValueError:
        raise ValueError("Invalid path setting. Please provide a valid path.")

    path_pwd = Path(__file__).parent
    if not results_path.is_absolute():
        results_path = path_pwd/results_path
    if not data_setpath.is_absolute():
        data_setpath = path_pwd/data_setpath
    if not solution_path.is_absolute():
        solution_path = path_pwd/solution_path
    if not eval_script_path.is_absolute():
        eval_script_path = path_pwd/eval_script_path
    
    results_path = results_path.resolve()
    data_setpath = data_setpath.resolve()
    solution_path = solution_path.resolve()
    eval_script_path = eval_script_path.resolve()

    config['results_path'] = results_path
    config['dataset_path'] = data_setpath
    config['solution_path'] = solution_path
    config['eval_script_path'] = eval_script_path

    return config


def sanitize_model_name(model: str) -> str:
    """Convert model name to valid folder name."""
    return model.replace('/', '-').replace('.', '.')


def validate_eval_script(eval_script_path: Path) -> None:
    """
    Validate that the evaluation script returns required fields.
    
    This function loads the user's my_eval.py and tests it with mock data
    to ensure it returns all required fields: raw_response, extracted_answer, usage.
    
    Args:
        eval_script_path: Path to my_eval.py file
    
    Raises:
        ValueError: If validation fails (missing imports, missing function, wrong return format)
        ImportError: If required dependencies cannot be imported
    """
    import importlib.util
    import sys
    
    print(f"  Validating eval script: {eval_script_path.name}")
    
    # Load the module dynamically
    spec = importlib.util.spec_from_file_location("my_eval", eval_script_path)
    if spec is None or spec.loader is None:
        raise ValueError(f"Cannot load eval script: {eval_script_path}")
    
    module = importlib.util.module_from_spec(spec)
    sys.modules["my_eval"] = module
    
    try:
        if spec.loader:
            spec.loader.exec_module(module)
    except Exception as e:
        raise ValueError(f"Error loading eval script: {e}")
    
    # Check if evaluate_question function exists
    if not hasattr(module, 'evaluate_question'):
        raise ValueError("evaluate_question() function not found in eval script")
    
    # Create a mock client with a dummy chat_completion method
    class MockClient:
        def __init__(self):
            self.request_count = 0
            self.cumulative_cost = 0.0
            self.total_tokens = 0
            self.total_prompt_tokens = 0
            self.total_completion_tokens = 0
            self.total_reasoning_tokens = 0
            self.total_cached_tokens = 0
        
        def chat_completion(self, **kwargs):
            self.request_count += 1
            cost = 0.0001
            prompt_toks = 50
            completion_toks = 50
            total_toks = 100
            
            self.cumulative_cost += cost
            self.total_tokens += total_toks
            self.total_prompt_tokens += prompt_toks
            self.total_completion_tokens += completion_toks
            
            return {
                'choices': [{
                    'message': {
                        'content': '{"answer": ["a"], "reasoning": "Test response"}'
                    },
                    'finish_reason': 'stop'
                }],
                'usage': {
                    'total_tokens': total_toks,
                    'prompt_tokens': prompt_toks,
                    'completion_tokens': completion_toks
                }
            }
        
        def get_usage_summary(self):
            return {
                'request_count': self.request_count,
                'cumulative_cost': self.cumulative_cost,
                'total_tokens': self.total_tokens,
                'total_prompt_tokens': self.total_prompt_tokens,
                'total_completion_tokens': self.total_completion_tokens,
                'total_reasoning_tokens': self.total_reasoning_tokens,
                'total_cached_tokens': self.total_cached_tokens,
                'average_cost_per_request': self.cumulative_cost / self.request_count if self.request_count > 0 else 0
            }
    
    # Test with mock data
    mock_question = "Test question"
    mock_client = MockClient()
    mock_model = "test/model"
    mock_config = {'temperature': 1.0}
    
    try:
        result = module.evaluate_question(
            question=mock_question,
            client=mock_client,
            model=mock_model,
            config=mock_config
        )
    except Exception as e:
        raise ValueError(f"Error calling evaluate_question(): {e}")
    
    # Verify required fields
    required_fields = ['raw_response', 'extracted_answer', 'usage']
    missing_fields = [f for f in required_fields if f not in result]
    
    if missing_fields:
        raise ValueError(
            f"evaluate_question() missing required fields: {missing_fields}. "
            f"Returned keys: {list(result.keys())}"
        )
    
    # Verify field types
    if not isinstance(result['raw_response'], (str, dict)):
        raise ValueError(f"raw_response must be str or dict, got {type(result['raw_response'])}")

    if not isinstance(result['extracted_answer'], str):
        raise ValueError(f"extracted_answer must be str, got {type(result['extracted_answer'])}")

    if not isinstance(result['usage'], dict):
        raise ValueError(f"usage must be dict, got {type(result['usage'])}")

    print(f"  [OK] Eval script validation passed")


def generate_config(model: str, settings: dict, model_folder: Path) -> dict:
    """Generate model-specific config.json."""
    return {
        'model': model,
        'llm_script': str(model_folder / 'my_eval.py'),
        'temperature': settings['temperature'],
        'max_tokens': settings['max_tokens'],
        'max_reasoning_tokens': settings['max_reasoning_tokens'],
        'num_repetitions': settings['num_repetitions'],
        'dataset_path': str(settings['dataset_path']),
        'solution_path': str(settings['solution_path']),
        'testing_mode': settings['testing_mode'],
        'message': settings.get('message'),
        'enable_parallel': settings.get('enable_parallel', False),
        'max_workers': settings.get('max_workers_per_model', None),
        'rate_limit_seconds': settings.get('rate_limit_seconds', 3.0),
        'results_path': str(settings['results_path'])  # Store results_path for resolving relative paths
    }


def create_model_folder(model: str, settings: dict) -> Path:
    """Create timestamped model folder with all required files."""
    sanitized_name = sanitize_model_name(model)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    model_folder = Path(settings['results_path']) / f'{sanitized_name}_{timestamp}'
    model_folder.mkdir(parents=True, exist_ok=True)

    # Copy eval script from settings path
    eval_src = Path(settings['eval_script_path'])
    if not eval_src.exists():
        raise FileNotFoundError(f"Eval script not found: {eval_src}")
    shutil.copy(eval_src, model_folder / 'my_eval.py')

    # Validate the eval script returns required fields
    try:
        validate_eval_script(eval_src)
    except (ValueError, ImportError) as e:
        raise ValueError(f"Eval script validation failed for {eval_src.name}: {e}")

    # Generate and save config.json (no system_prompt.md - prompts in my_eval.py)
    config = generate_config(model, settings, model_folder)
    config_path = model_folder / 'config.json'

    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)

    return model_folder


def verify_dataset_exists(config: dict, model_folder: Path) -> tuple[bool, str]:
    
    dataset_path = Path(config['dataset_path'])
    solution_path = Path(config['solution_path'])
    
    if not dataset_path.exists():
        return False, f"Dataset not found: {dataset_path}"

    if not config.get('testing_mode', False) and not solution_path.exists():
        return False, f"Solution not found: {solution_path}"

    return True, ""


# ============================================================================
# BENCHMARK EXECUTION
# ============================================================================

def run_single_model(model: str, model_folder: Path, settings: dict) -> dict:
    """Run benchmark for a single model (executed by worker)."""
    sanitized_name = sanitize_model_name(model)
    start_time = time.time()

    try:
        # Load config
        config_path = model_folder / 'config.json'
        with open(config_path, 'r') as f:
            config = json.load(f)

        # Verify dataset exists
        dataset_ok, error_msg = verify_dataset_exists(config, model_folder)
        if not dataset_ok:
            return {
                'model': model,
                'sanitized_name': sanitized_name,
                'status': 'failed',
                'error': error_msg,
                'mean_accuracy': None,
                'std_accuracy': None,
                'total_cost': None,
                'total_tokens': None,
                'duration_seconds': 0,
                'folder': str(model_folder)
            }

        # Load dataset
        dataset_path = Path(config['dataset_path'])        
        dataset_df = pd.read_csv(dataset_path)

        # Set rate limit from config (used by GlobalRateLimiter)
        rate_limit_seconds = config.get('rate_limit_seconds', 1.0)
        os.environ['OPENROUTER_RATE_LIMIT_SECONDS'] = str(rate_limit_seconds)

        # Initialize client, runner, logger
        # Note: Client automatically uses GlobalRateLimiter singleton with rate limit from env var
        client = OpenRouterClient()
        runner = BenchmarkRunner(client, str(model_folder), config)
        logger = BenchmarkLogger(str(model_folder), config)

        # Run all repetitions with optional parallel execution
        predictions_df = runner.run_benchmark(
            dataset_df=dataset_df,
            num_repetitions=config['num_repetitions'],
            logger=logger,
            enable_parallel=config.get('enable_parallel', False),
            max_workers=config.get('max_workers'),
            rate_limit_seconds=config.get('rate_limit_seconds', 3.0)
        )

        # Extract answers from predictions_df for each run
        run_accuracies = []
        run_kaggle_scores = []

        for run_idx in range(1, config['num_repetitions'] + 1):
            # Update JSON files with extracted answers (already extracted by user's my_eval.py)
            json_path = model_folder / f"run_{run_idx}_results.json"
            with open(json_path, 'r', encoding='utf-8') as f:
                run_results = json.load(f)

            # Get extracted answers from results
            extracted_answers = []
            for result in run_results:
                if 'extracted_answer' in result:
                    extracted_answers.append(result['extracted_answer'])

            # Use prediction_{run_idx} column (not extracted_answer_{run_idx})
            predictions_df[f'prediction_{run_idx}'] = extracted_answers

            # Calculate accuracy for this run (if not in testing mode)
            if not config.get('testing_mode', False):
                results_path = Path(config.get('results_path', model_folder))
                solution_path = Path(config['solution_path'])                
                correct_df = pd.read_csv(solution_path)

                correct_count = 0
                total_count = 0
                for idx, row in predictions_df.iterrows():
                    qid = row['question_id']
                    pred = row.get(f'prediction_{run_idx}', '')
                    correct_row = correct_df[correct_df['question_id'] == qid]
                    if not correct_row.empty:
                        correct_ans = correct_row['answer'].values[0]
                        # Use are_answers_equal logic
                        pred_norm = str(pred).strip().lower().replace(", ", ",")
                        correct_norm = str(correct_ans).strip().lower().replace(", ", ",")
                        pred_set = set(p.strip() for p in pred_norm.split(',') if p.strip())
                        correct_set = set(c.strip() for c in correct_norm.split(',') if c.strip())
                        if pred_set == correct_set:
                            correct_count += 1
                        total_count += 1

                if total_count > 0:
                    accuracy = correct_count / total_count
                    run_accuracies.append(accuracy)

        # Create solution.csv with only question_id and prediction_{run_idx} columns
        solution_columns = ['question_id'] + [f'prediction_{i}' for i in range(1, config['num_repetitions'] + 1)]
        solution_df = predictions_df[solution_columns].copy()

        # Save solution.csv
        solution_path = model_folder / 'solution.csv'
        solution_df.to_csv(solution_path, index=False)

        # If testing mode, skip all performance calculation and report generation
        if config.get('testing_mode', False):
            # Get usage summary
            if config.get('enable_parallel', False) and config['num_repetitions'] > 1:
                usage_summary = predictions_df.attrs.get('aggregated_usage', client.get_usage_summary())
            else:
                usage_summary = client.get_usage_summary()

            # Calculate average cost per run and create solution_kaggle.csv
            avg_cost_per_run = usage_summary['cumulative_cost'] / config['num_repetitions']
            if create_solution_kaggle_csv(model_folder, avg_cost_per_run):
                print(f"  [Created] solution_kaggle.csv (avg_cost_per_run=${avg_cost_per_run:.6f})")
            else:
                print(f"  [Warning] Failed to create solution_kaggle.csv")

            duration = time.time() - start_time

            return {
                'model': model,
                'sanitized_name': sanitized_name,
                'status': 'success',
                'error': None,
                'mean_accuracy': None,  # No accuracy in testing mode
                'std_accuracy': None,
                'total_cost': usage_summary['cumulative_cost'],
                'total_tokens': usage_summary['total_tokens'],
                'num_repetitions': config['num_repetitions'],
                'duration_seconds': duration,
                'folder': str(model_folder)
            }

        # Calculate final statistics (only if not testing mode)
        # Get usage summary - check if parallel mode was used
        if config.get('enable_parallel', False) and config['num_repetitions'] > 1:
            # Parallel mode - use aggregated usage from DataFrame attrs
            usage_summary = predictions_df.attrs.get('aggregated_usage', client.get_usage_summary())
        else:
            # Sequential mode - use client's usage summary
            usage_summary = client.get_usage_summary()

        duration = time.time() - start_time

        mean_accuracy = None
        std_accuracy = None
        mean_kaggle_score = None

        if run_accuracies:
            import numpy as np
            mean_accuracy = np.mean(run_accuracies)
            if len(run_accuracies) > 1:
                std_accuracy = np.std(run_accuracies)

        # Calculate Mean Kaggle Score using mean accuracy and average cost per run
        if run_accuracies and usage_summary:
            import numpy as np
            calculate_kaggle_score_func = _get_calculate_kaggle_score()
            avg_cost_per_run = usage_summary['cumulative_cost'] / config['num_repetitions']
            mean_kaggle_score = calculate_kaggle_score_func(mean_accuracy, avg_cost_per_run)

        # Generate reports if not in testing mode
        if not config.get('testing_mode', False):
            results_path = Path(config.get('results_path', model_folder))
            solution_path = Path(config['solution_path'])
            correct_df = pd.read_csv(solution_path)

            logger.generate_result_report(
                predictions_df,
                correct_df,
                usage_summary,
                config['num_repetitions'],
                config.get('message')
            )

            logger.generate_wrong_answers_report(
                predictions_df,
                correct_df,
                dataset_df
            )

        return {
            'model': model,
            'sanitized_name': sanitized_name,
            'status': 'success',
            'error': None,
            'mean_accuracy': mean_accuracy,
            'std_accuracy': std_accuracy,
            'mean_kaggle_score': mean_kaggle_score,
            'total_cost': usage_summary['cumulative_cost'],
            'total_tokens': usage_summary['total_tokens'],
            'num_repetitions': config['num_repetitions'],
            'duration_seconds': duration,
            'folder': str(model_folder)
        }

    except Exception as e:
        duration = time.time() - start_time
        return {
            'model': model,
            'sanitized_name': sanitized_name,
            'status': 'failed',
            'error': str(e),
            'mean_accuracy': None,
            'std_accuracy': None,
            'total_cost': None,
            'total_tokens': None,
            'duration_seconds': duration,
            'folder': str(model_folder)
        }


def run_parallel_benchmarks(models: List[str], workers: int, settings: dict) -> List[dict]:
    """Run benchmarks in parallel with ThreadPoolExecutor."""
    # Setup paths
    results_path = Path(settings['results_path'])

    # Create results directory
    results_path.mkdir(parents=True, exist_ok=True)

    print(f"\nCreating model folders in {results_path}...")

    # Create all model folders upfront
    model_folders = {}
    for model in models:
        try:
            model_folder = create_model_folder(model, settings)
            model_folders[model] = model_folder
            print(f"  [OK] {sanitize_model_name(model)}")
        except Exception as e:
            print(f"  [FAILED] {model}: {e}")
            continue

    if not model_folders:
        print("\nError: No model folders created successfully")
        return []

    # Verify datasets
    print(f"\nVerifying datasets...")
    valid_models = []
    for model, model_folder in model_folders.items():
        config_path = model_folder / 'config.json'
        with open(config_path, 'r') as f:
            config = json.load(f)

        dataset_ok, error_msg = verify_dataset_exists(config, model_folder)
        if dataset_ok:
            valid_models.append(model)
        else:
            print(f"  [FAILED] {model}: {error_msg}")

    if not valid_models:
        print("\nError: No valid models (all datasets missing)")
        return []

    print(f"  [OK] All {len(valid_models)} datasets verified")

    # Run benchmarks in parallel with tqdm position tracking
    print(f"\nRunning benchmarks in parallel ({workers} workers)...")
    results = []

    with ThreadPoolExecutor(max_workers=workers) as executor:
        # Submit all jobs
        futures = {
            executor.submit(run_single_model, model, model_folders[model], settings): model
            for model in valid_models
        }

        # Use tqdm with position tracking for clean output
        with tqdm(total=len(futures), desc="Overall Progress", position=0, leave=False) as pbar:
            for future in as_completed(futures):
                model = futures[future]
                try:
                    result = future.result()
                    results.append(result)

                    # Update progress bar
                    pbar.update(1)
                    pbar.refresh()

                    # Print result below progress bar using tqdm.write()
                    if result['status'] == 'success':
                        acc_str = f"{result['mean_accuracy']:.4f}" if result['mean_accuracy'] else "N/A"
                        kaggle_str = f"{result['mean_kaggle_score']:.4f}" if result.get('mean_kaggle_score') else "N/A"
                        tqdm.write(f"[OK] {model}: Accuracy={acc_str}, Kaggle={kaggle_str}, Cost=${result['total_cost']:.4f}")
                    else:
                        tqdm.write(f"[FAILED] {model}: FAILED - {result['error']}")

                except Exception as e:
                    tqdm.write(f"[FAILED] {model}: EXCEPTION - {e}")
                    results.append({
                        'model': model,
                        'sanitized_name': sanitize_model_name(model),
                        'status': 'failed',
                        'error': str(e),
                        'mean_accuracy': None,
                        'std_accuracy': None,
                        'total_cost': None,
                        'total_tokens': None,
                        'duration_seconds': 0,
                        'folder': str(model_folders[model])
                    })

    return results


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main execution - load config from JSON file."""
    # Parse CLI arguments
    parser = argparse.ArgumentParser(
        description='Batch test multiple LLM models with parallel execution'
    )
    parser.add_argument(
        '--config',
        type=str,
        default=CONFIG_PATH,
        help=f'Path to JSON config file (default: {CONFIG_PATH})'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    try:
        settings = load_config(args.config)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in config file: {e}")
        sys.exit(1)
    
    # Transform all the paths into absolute paths
    settings = parse_path_settings(settings)
    
    models = settings['models']

    # Print header
    print("=" * 80)
    print("BATCH MODEL TESTING")
    print("=" * 80)
    print(f"Config file: {args.config}")
    print(f"Models to test: {len(models)}")
    print(f"Workers (model-level): {settings['workers']}")
    print(f"Repetitions per model: {settings['num_repetitions']}")
    print(f"Parallel mode: {settings.get('enable_parallel', False)}")
    if settings.get('enable_parallel', False):
        print(f"  Max workers per model: {settings.get('max_workers_per_model', 'auto')}")
        print(f"  Rate limit: {settings.get('rate_limit_seconds', 3.0)} seconds/request")
    print(f"Testing mode: {settings['testing_mode']}")
    print(f"Results path: {settings['results_path']}")
    print("=" * 80)

    # Run benchmarks
    results = run_parallel_benchmarks(models, settings['workers'], settings)

    if not results:
        print("\nNo results generated")
        sys.exit(1)

    # Print summary statistics
    successful = [r for r in results if r['status'] == 'success']
    failed = [r for r in results if r['status'] == 'failed']

    total_cost = sum(r['total_cost'] or 0 for r in successful)
    total_tokens = sum(r['total_tokens'] or 0 for r in successful)
    total_runs = sum(r.get('num_repetitions', settings['num_repetitions']) for r in successful)

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    if successful:
        print(f"Total Cost: ${total_cost:.4f} (Avg ${total_cost / total_runs:.4f} per run)")
        print(f"Total Tokens: {total_tokens:,} (Avg {total_tokens / total_runs:.0f} per run)")
    print("=" * 80)

    # Generate summary files using create_summary_report functions
    results_dir = Path(settings['results_path'])

    print(f"\n{'=' * 80}")
    print("GENERATING SUMMARY REPORTS")
    print(f"{'=' * 80}")

    # Scan for result_analysis.md files and generate summaries
    summary_results = summary_gen.scan_directory(results_dir)

    if summary_results:
        summary_md_path = results_dir / 'summary.md'

        summary_gen.generate_summary_markdown(summary_results, summary_md_path, results_dir)

        print(f"\nGenerated summary files:")
        print(f"  - {summary_md_path}")
    else:
        print("\nNo result_analysis.md files found - skipping summary generation")

    print(f"\nResults saved to: {results_dir}")


if __name__ == '__main__':
    main()
