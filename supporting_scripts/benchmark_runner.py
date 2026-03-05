"""
Benchmark runner with user script loading.
"""
import sys
import importlib.util
from pathlib import Path
from typing import Dict, List
import pandas as pd
from tqdm import tqdm
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


class RateLimiter:
    """Thread-safe rate limiter for API calls.
    
    Ensures that requests across all workers respect a minimum interval
    between API calls to stay within rate limits.
    
    Args:
        min_interval: Minimum seconds between API calls (default: 3.0 = 20 req/min)
    """
    
    def __init__(self, min_interval=3.0):
        self.min_interval = min_interval
        self.lock = threading.Lock()
        self.last_call_time = None
    
    def acquire(self):
        """Acquire permission to make an API call, blocking if necessary."""
        with self.lock:
            now = time.time()
            if self.last_call_time:
                elapsed = now - self.last_call_time
                if elapsed < self.min_interval:
                    sleep_time = self.min_interval - elapsed
                    time.sleep(sleep_time)
            self.last_call_time = time.time()


class BenchmarkRunner:
    """Orchestrates benchmark execution using user-defined evaluation scripts."""

    def __init__(self, client, folder_path: str, config: dict):
        """
        Initialize benchmark runner.

        Args:
            client: OpenRouterClient instance
            folder_path: Path to experiment folder
            config: Configuration dictionary
        """
        self.client = client
        self.folder_path = Path(folder_path)
        self.config = config
        self.llm_script_path = config.get('llm_script')
        if not self.llm_script_path:
            raise ValueError("llm_script must be specified in config")

    def load_user_script_module(self):
        """Load user's evaluation script using importlib."""
        script_path = Path(self.llm_script_path)
        if not script_path.exists():
            raise FileNotFoundError(f"Evaluation script not found: {self.llm_script_path}")

        spec = importlib.util.spec_from_file_location("user_eval", script_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules["user_eval"] = module
        spec.loader.exec_module(module)
        return module

    def run_single_question(self, question: str, question_id: int, rate_limiter=None) -> dict:
        """
        Call user's evaluate_question function.

        Args:
            question: Question text
            question_id: Question ID
            rate_limiter: Optional rate limiter (overrides client's rate limiter if provided)
                         Note: By default, the client uses GlobalRateLimiter singleton automatically.

        Returns:
            Dictionary with question_id, question, raw_response, extracted_answer, usage
        """
        module = self.load_user_script_module()

        try:
            result = module.evaluate_question(
                question=question,
                client=self.client,
                model=self.config['model'],
                config=self.config
            )

            # Validate required fields
            required = ['raw_response', 'extracted_answer', 'usage']
            for field in required:
                if field not in result:
                    raise ValueError(f"User script must return '{field}'")

            result['question_id'] = question_id
            result['question'] = question
            return result

        except Exception as e:
            # Log error and return empty result
            print(f"Error in user script for question {question_id}: {e}")
            return {
                'question_id': question_id,
                'question': question,
                'raw_response': '',
                'extracted_answer': '',
                'usage': {}
            }

    def run_benchmark(self, dataset_df: pd.DataFrame, num_repetitions: int, logger, 
                     enable_parallel=False, max_workers=None, rate_limit_seconds=3.0) -> pd.DataFrame:
        """
        Run full benchmark and return predictions DataFrame.

        Args:
            dataset_df: Dataset DataFrame with questions
            num_repetitions: Number of repetitions to run
            logger: BenchmarkLogger instance for saving results
            enable_parallel: If True, run repetitions in parallel (default: False)
            max_workers: Maximum parallel workers (default: num_repetitions)
            rate_limit_seconds: Minimum seconds between API calls (default: 3.0)

        Returns:
            DataFrame with predictions for all runs
        """
        df_results = pd.DataFrame()
        df_results['question_id'] = dataset_df['question_id'].values

        if not enable_parallel or num_repetitions == 1:
            # SEQUENTIAL MODE (original behavior)
            for run_idx in range(1, num_repetitions + 1):
                print(f"\n{'='*80}")
                print(f"STARTING RUN {run_idx}/{num_repetitions}")
                print(f"{'='*80}\n")

                results = []

                for idx, row in tqdm(dataset_df.iterrows(), total=len(dataset_df), desc=f"Run {run_idx}"):
                    question = row['question']
                    question_id = row['question_id']

                    result = self.run_single_question(question, question_id)
                    results.append(result)

                # Save results to JSON
                logger.log_run_results(run_idx, results)

                # Extract answers from raw responses (done after all runs in main script)
                # For now, just store raw responses
                raw_responses = [r['raw_response'] for r in results]
                df_results[f"prediction_{run_idx}"] = raw_responses
        else:
            # PARALLEL MODE (new)
            from supporting_scripts import OpenRouterClient
            
            print(f"\n{'='*80}")
            print(f"PARALLEL EXECUTION MODE")
            print(f"{'='*80}")
            print(f"Running {num_repetitions} runs in parallel...")
            print(f"Workers: {max_workers or num_repetitions}")
            print(f"Rate limiting: {rate_limit_seconds} seconds per request (global)")
            print(f"{'='*80}\n")
            
            # Note: Rate limiting is now handled automatically by OpenRouterClient
            # using the GlobalRateLimiter singleton. No need to create/pass rate limiter manually.
            # All clients across all models share the same global rate limiter.
            
            # Create client factory for workers
            def client_factory():
                # Each client automatically uses GlobalRateLimiter singleton
                return OpenRouterClient()
            
            # Prepare arguments for each worker
            worker_args = [
                (run_idx, dataset_df, client_factory, self.folder_path, self.config)
                for run_idx in range(1, num_repetitions + 1)
            ]
            
            # Thread pool for parallel execution
            max_workers = max_workers or num_repetitions
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all runs
                futures = {
                    executor.submit(run_single_run_worker, *args): args[0]
                    for args in worker_args
                }
                
                # Collect results as they complete
                run_results = {}
                usage_summaries = []
                
                print("\n" + "="*80)
                print("PARALLEL EXECUTION - Runs will complete in random order")
                print("="*80 + "\n")
                
                for future in as_completed(futures):
                    run_idx = futures[future]
                    try:
                        run_idx, results, usage_summary = future.result()
                        
                        # Store results
                        run_results[run_idx] = results
                        usage_summaries.append(usage_summary)
                        
                        # Save results to JSON for this run
                        logger.log_run_results(run_idx, results)
                        
                        # Extract and store answers
                        raw_responses = [r['raw_response'] for r in results]
                        df_results[f"prediction_{run_idx}"] = raw_responses
                        
                        # Print run completion message immediately
                        print(f"\n{'='*80}")
                        print(f"RUN {run_idx} COMPLETED")
                        print(f"{'='*80}")
                        print(f"Cost: ${usage_summary['cumulative_cost']:.4f}")
                        print(f"Tokens: {usage_summary['total_tokens']:,}")
                        print(f"Requests: {usage_summary['request_count']}")
                        print(f"{'='*80}\n")
                        
                    except Exception as e:
                        print(f"ERROR in Run {run_idx}: {e}")
                        import traceback
                        traceback.print_exc()
            
            # Aggregate usage statistics from all workers
            aggregated_usage = aggregate_usage_summaries(usage_summaries)
            
            # Store aggregated stats in DataFrame attrs for retrieval by main script
            df_results.attrs['aggregated_usage'] = aggregated_usage
            
            print(f"\n{'='*80}")
            print("ALL RUNS COMPLETED - AGGREGATED STATISTICS")
            print(f"{'='*80}")
            print(f"Total Cost: ${aggregated_usage['cumulative_cost']:.4f}")
            print(f"Total Tokens: {aggregated_usage['total_tokens']:,}")
            print(f"Total Requests: {aggregated_usage['request_count']}")
            print(f"{'='*80}\n")

        return df_results


def run_single_run_worker(run_idx, dataset_df, client_factory, folder_path, config):
    """
    Execute a single run - worker function for ThreadPoolExecutor.

    Args:
        run_idx: Run index (1-based)
        dataset_df: DataFrame with questions
        client_factory: Function that creates OpenRouterClient instances
        folder_path: Path to experiment folder
        config: Configuration dictionary

    Returns:
        tuple: (run_idx, results_list, usage_summary_dict)
    
    Note:
        Rate limiting is handled automatically by OpenRouterClient using the
        GlobalRateLimiter singleton. No need to pass rate_limiter explicitly.
    """
    from supporting_scripts import OpenRouterClient
    
    client = client_factory()
    runner = BenchmarkRunner(client, folder_path, config)
    results = []
    
    with tqdm(total=len(dataset_df), desc=f"Run {run_idx}", 
              position=run_idx, leave=True) as pbar:
        for idx, row in dataset_df.iterrows():
            question = row['question']
            question = str(question).strip() if not isinstance(question, str) else question.strip()
            question_id = row['question_id']
            
            result = runner.run_single_question(question, question_id)
            results.append(result)
            
            pbar.update(1)
            if result.get('usage', {}).get('cost'):
                pbar.set_postfix({"Cost": f"${result['usage']['cost']:.4f}"})
    
    usage_summary = client.get_usage_summary()
    return run_idx, results, usage_summary


def aggregate_usage_summaries(summaries):
    """
    Aggregate usage summaries from multiple workers.
    
    Args:
        summaries: List of usage summary dictionaries
    
    Returns:
        Aggregated usage dictionary
    """
    return {
        'cumulative_cost': sum(s.get('cumulative_cost', 0) for s in summaries),
        'total_tokens': sum(s.get('total_tokens', 0) for s in summaries),
        'total_prompt_tokens': sum(s.get('total_prompt_tokens', 0) for s in summaries),
        'total_completion_tokens': sum(s.get('total_completion_tokens', 0) for s in summaries),
        'total_reasoning_tokens': sum(s.get('total_reasoning_tokens', 0) for s in summaries),
        'total_cached_tokens': sum(s.get('total_cached_tokens', 0) for s in summaries),
        'request_count': sum(s.get('request_count', 0) for s in summaries),
    }
