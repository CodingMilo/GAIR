"""
Benchmark logger for saving results and generating reports.
"""
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd
import re
import numpy as np


def _get_calculate_kaggle_score():
    """Lazy import of calculate_kaggle_score to avoid circular dependencies."""
    import sys
    import importlib.util
    from pathlib import Path as PathImport
    # benchmark_logger.py is in supporting_scripts/, eval_code is in supporting_scripts/test_eval_code/
    _eval_code_file = PathImport(__file__).parent / 'test_eval_code' / 'eval_code.py'
    
    spec = importlib.util.spec_from_file_location("eval_code", _eval_code_file)
    module = importlib.util.module_from_spec(spec)
    sys.modules["eval_code"] = module
    spec.loader.exec_module(module)
    
    return module.calculate_kaggle_score


def normalize_answer(answer):
    """Normalize answer string for comparison."""
    if pd.isna(answer):
        return ""
    return str(answer).strip().lower().replace(", ", ",")


def are_answers_equal(pred, correct):
    """Check if predicted answer matches correct answer."""
    pred_norm = normalize_answer(pred)
    correct_norm = normalize_answer(correct)

    pred_set = set(p.strip() for p in pred_norm.split(',') if p.strip())
    correct_set = set(c.strip() for c in correct_norm.split(',') if c.strip())

    return pred_set == correct_set


def parse_question_choices(question_text):
    """Parse question and choices from the question text."""
    choices_pattern = r'\[Choices\]:\s*(.*)$'
    choices_match = re.search(choices_pattern, question_text, re.MULTILINE | re.DOTALL)

    if choices_match:
        choices_text = choices_match.group(1).strip()
        question_only = re.sub(choices_pattern, '', question_text, flags=re.MULTILINE | re.DOTALL).strip()

        choices = {}
        for choice in choices_text.split('|'):
            choice = choice.strip()
            if choice and choice[0] in 'abcdefghijklmnopqrstuvwxyz':
                choice_letter = choice[0].lower()
                choice_text = choice[2:].strip() if len(choice) > 2 else choice[1:].strip()
                choices[choice_letter] = choice_text

        return question_only, choices
    return question_text, {}


class BenchmarkLogger:
    """Handle all logging, CSV export, and report generation."""

    def __init__(self, folder_path: str, config: dict):
        """
        Initialize benchmark logger.

        Args:
            folder_path: Path to experiment folder
            config: Configuration dictionary
        """
        self.folder_path = Path(folder_path)
        self.config = config
        self.start_time = datetime.now()

    def log_run_results(self, run_idx: int, results: List[dict]) -> str:
        """
        Save all question results for one run to JSON.

        Args:
            run_idx: Run index (1-based)
            results: List of result dictionaries

        Returns:
            Path to saved JSON file
        """
        output_path = self.folder_path / f"run_{run_idx}_results.json"

        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)

        return str(output_path)

    def save_solution_csv(self, predictions_df: pd.DataFrame) -> str:
        """
        Save aggregated predictions to CSV.

        Args:
            predictions_df: DataFrame with predictions for all runs

        Returns:
            Path to saved CSV file
        """
        output_path = self.folder_path / "solution.csv"
        predictions_df.to_csv(output_path, index=False)
        return str(output_path)

    def save_config(self, config: dict) -> str:
        """
        Save/overwrite config.json.

        Args:
            config: Configuration dictionary

        Returns:
            Path to saved config file
        """
        output_path = self.folder_path / "config.json"
        with open(output_path, 'w') as f:
            json.dump(config, f, indent=2)
        return str(output_path)

    def load_json_logs(self) -> Dict[int, List[dict]]:
        """
        Load all JSON log files and organize by question_id.

        Returns:
            Dictionary mapping question_id to list of entries from all runs
        """
        question_results = {}

        json_files = sorted(self.folder_path.glob("run_*_results.json"))

        for json_file in json_files:
            with open(json_file, 'r', encoding='utf-8') as f:
                results = json.load(f)

            for entry in results:
                qid = entry['question_id']
                if qid not in question_results:
                    question_results[qid] = []
                question_results[qid].append(entry)

        return question_results

    def calculate_run_usage(self, run_idx: int) -> dict:
        """
        Calculate total usage statistics for a specific run.

        Args:
            run_idx: Run index (1-based)

        Returns:
            Dictionary with cost, tokens for the run
        """
        json_file = self.folder_path / f"run_{run_idx}_results.json"

        if not json_file.exists():
            return {
                'cost': 0,
                'total_tokens': 0,
                'prompt_tokens': 0,
                'completion_tokens': 0,
                'request_count': 0
            }

        with open(json_file, 'r', encoding='utf-8') as f:
            results = json.load(f)

        total_cost = 0
        total_tokens = 0
        prompt_tokens = 0
        completion_tokens = 0
        request_count = len(results)

        for entry in results:
            usage = entry.get('usage', {}) or {}
            total_cost += usage.get('cost', 0) or 0
            total_tokens += usage.get('total_tokens', 0) or 0
            prompt_tokens += usage.get('prompt_tokens', 0) or 0
            completion_tokens += usage.get('completion_tokens', 0) or 0

        return {
            'cost': total_cost,
            'total_tokens': total_tokens,
            'prompt_tokens': prompt_tokens,
            'completion_tokens': completion_tokens,
            'request_count': request_count
        }

    def generate_result_report(
        self,
        predictions_df: pd.DataFrame,
        correct_df: pd.DataFrame,
        usage_summary: dict,
        num_repetitions: int,
        message: Optional[str] = None
    ) -> str:
        """
        Generate result_analysis.md.

        Args:
            predictions_df: DataFrame with predictions
            correct_df: DataFrame with correct answers
            usage_summary: Usage summary from client
            num_repetitions: Number of repetitions

        Returns:
            Path to generated markdown file
        """
        output_path = self.folder_path / "result_analysis.md"
        end_time = datetime.now()

        report_lines = []
        report_lines.append("# Solution Analysis Report\n")
        report_lines.append(f"Generated: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        report_lines.append("## Configuration\n\n")
        report_lines.append("### Model Parameters\n")
        report_lines.append(f"- **Model**: {self.config.get('model', 'N/A')}\n")
        report_lines.append(f"- **Temperature**: {self.config.get('temperature', 'N/A')}\n")
        report_lines.append(f"- **Max Tokens**: {self.config.get('max_tokens', 'None')}\n")
        report_lines.append(f"- **Max Reasoning Tokens**: {self.config.get('max_reasoning_tokens', 'N/A')}\n\n")

        report_lines.append("### Dataset\n")
        report_lines.append(f"- **Test Dataset**: {self.config.get('dataset_path', 'N/A')}\n")
        report_lines.append(f"- **Solution File**: {self.config.get('solution_path', 'N/A')}\n\n")

        report_lines.append("### Execution\n")
        report_lines.append(f"- **Number of Runs**: {num_repetitions}\n")
        report_lines.append(f"- **Start Time**: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        report_lines.append(f"- **End Time**: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        duration = end_time - self.start_time
        report_lines.append(f"- **Duration**: {duration}\n\n")

        if message:
            report_lines.append("### Message\n")
            report_lines.append(f"{message}\n\n")

        report_lines.append("## Results Summary\n\n")
        # Calculate accuracy per run
        run_accuracies = []
        run_kaggle_scores = []
        run_usage_data = []

        for run_idx in range(1, num_repetitions + 1):
            extracted_col = f'prediction_{run_idx}'
            run_accuracy = None
            total_count = 0
            if extracted_col in predictions_df.columns:
                correct_count = 0
                total_count = 0
                for idx, row in predictions_df.iterrows():
                    qid = row['question_id']
                    pred = row.get(extracted_col, '')
                    correct_row = correct_df[correct_df['question_id'] == qid]
                    if not correct_row.empty:
                        correct_ans = correct_row['answer'].values[0]
                        if are_answers_equal(pred, correct_ans):
                            correct_count += 1
                        total_count += 1
                if total_count > 0:
                    run_accuracy = correct_count / total_count
                    run_accuracies.append(run_accuracy)

            # Get usage data for this run
            run_usage = self.calculate_run_usage(run_idx)
            run_usage_data.append(run_usage)

            # Calculate Kaggle score for this run (if we have accuracy)
            if run_accuracy is not None and run_usage['cost'] > 0:
                calculate_kaggle_score = _get_calculate_kaggle_score()
                cost_per_run = run_usage['cost']
                run_kaggle_score = calculate_kaggle_score(run_accuracy, cost_per_run)
                run_kaggle_scores.append(run_kaggle_score)
            else:
                # If no accuracy or cost, append None or 0
                run_kaggle_scores.append(0.0)

        # Calculate overall statistics
        import numpy as np
        if run_accuracies:
            mean_accuracy = np.mean(run_accuracies)
            if num_repetitions > 1:
                std_accuracy = np.std(run_accuracies)
                report_lines.append(f"- **Mean Accuracy**: {mean_accuracy:.4f} ± {std_accuracy:.4f}\n")
            else:
                report_lines.append(f"- **Accuracy**: {mean_accuracy:.4f}\n")

        # Calculate Mean Kaggle Score using mean accuracy and average cost per run
        # Formula: kaggle = mean_accuracy - 0.15 * (total_cost / n_runs)
        if run_accuracies and usage_summary:
            mean_accuracy = np.mean(run_accuracies)
            avg_cost_per_run = usage_summary['cumulative_cost'] / num_repetitions
            calculate_kaggle_score = _get_calculate_kaggle_score()
            mean_kaggle = calculate_kaggle_score(mean_accuracy, avg_cost_per_run)
            report_lines.append(f"- **Mean Kaggle Score**: {mean_kaggle:.4f}\n")

        total_tokens = usage_summary.get('total_tokens', 0)
        prompt_tokens = usage_summary.get('total_prompt_tokens', 0)
        completion_tokens = usage_summary.get('total_completion_tokens', 0)
        report_cost = usage_summary.get('cumulative_cost', 0)
        
        report_lines.append(f"- **Total Cost**: ${report_cost:.4f}\n")
        report_lines.append(f"- **Total Tokens**: {total_tokens:,}\n")
        report_lines.append(f"  - Prompt Tokens: {prompt_tokens:,}\n")
        report_lines.append(f"  - Completion Tokens: {completion_tokens:,}\n")
        report_lines.append(f"- **Total API Requests**: {usage_summary.get('request_count', 0)}\n\n")

        # Build performance per run table
        report_lines.append("## Performance per Run\n\n")
        header = "| Run | Accuracy | Kaggle Score | Correct / Total | Cost ($) | Tokens (Prompt + Completion) |\n"
        separator = "|-----|----------|--------------|-----------------|----------|-----------------------------|\n"
        report_lines.append(header)
        report_lines.append(separator)

        for run_idx in range(1, num_repetitions + 1):
            extracted_col = f'prediction_{run_idx}'
            usage_data = run_usage_data[run_idx - 1]

            if extracted_col in predictions_df.columns:
                correct_count = 0
                total_count = 0
                for idx, row in predictions_df.iterrows():
                    qid = row['question_id']
                    pred = row.get(extracted_col, '')
                    correct_row = correct_df[correct_df['question_id'] == qid]
                    if not correct_row.empty:
                        correct_ans = correct_row['answer'].values[0]
                        if are_answers_equal(pred, correct_ans):
                            correct_count += 1
                        total_count += 1
                if total_count > 0:
                    accuracy = correct_count / total_count
                    kaggle_str = f"{run_kaggle_scores[run_idx - 1]:.4f}" if run_idx - 1 < len(run_kaggle_scores) else "N/A"
                    cost_str = f"${usage_data['cost']:.4f}"
                    tokens_str = f"{usage_data['total_tokens']:,} ({usage_data['prompt_tokens']:,} + {usage_data['completion_tokens']:,})"
                    line = f"| {run_idx} | {accuracy:.4f} | {kaggle_str} | {correct_count} / {total_count} | {cost_str} | {tokens_str} |\n"
                else:
                    line = f"| {run_idx} | N/A | N/A | 0 / 0 | $0.0000 | 0 (0 + 0) |\n"
                report_lines.append(line)

        report_lines.append("\n## Cost Efficiency Analysis\n\n")

        # Overall metrics (always show)
        total_cost = usage_summary.get('cumulative_cost', 0)
        total_tokens = usage_summary.get('total_tokens', 0)

        report_lines.append("### Overall Metrics\n\n")
        if run_accuracies and mean_accuracy > 0:
            # Cost per 1 percentage point of accuracy
            cost_per_acc_pct = total_cost / num_repetitions / mean_accuracy
            # Tokens per 1 percentage point of accuracy
            tokens_per_acc_pct = total_tokens / num_repetitions / mean_accuracy / 100
            report_lines.append(f"- **Average cost per 1% Accuracy (dollar cents)**: ${cost_per_acc_pct:.6f}\n")
            report_lines.append(f"- **Average tokens per 1% Accuracy**: {tokens_per_acc_pct:.1f}\n")

        report_lines.append(f"- **Average Cost per Question**: ${total_cost / num_repetitions/ len(predictions_df):.6f}\n")
        report_lines.append(f"- **Average Tokens per Question**: {total_tokens / num_repetitions/len(predictions_df):.1f}\n\n")

        # Per-run average metrics
        if num_repetitions > 1 and run_usage_data:
            report_lines.append("### Average Per Run\n\n")
            avg_cost = sum(u['cost'] for u in run_usage_data) / len(run_usage_data)
            avg_tokens = sum(u['total_tokens'] for u in run_usage_data) / len(run_usage_data)
            avg_prompt = sum(u['prompt_tokens'] for u in run_usage_data) / len(run_usage_data)
            avg_completion = sum(u['completion_tokens'] for u in run_usage_data) / len(run_usage_data)

            report_lines.append(f"- **Average Cost per Run**: ${avg_cost:.6f}\n")
            report_lines.append(f"- **Average Tokens per Run**: {avg_tokens:.1f}\n")
            report_lines.append(f"  - Prompt Tokens: {avg_prompt:.1f}\n")
            report_lines.append(f"  - Completion Tokens: {avg_completion:.1f}\n")

        with open(output_path, 'w', encoding='utf-8') as f:
            f.writelines(report_lines)

        return str(output_path)

    def generate_wrong_answers_report(
        self,
        solution_df: pd.DataFrame,
        correct_df: pd.DataFrame,
        dataset_df: pd.DataFrame
    ) -> str:
        """
        Generate wrong_answers.md grouped by run number.

        Args:
            solution_df: DataFrame with predictions and extracted answers
            correct_df: DataFrame with correct answers
            dataset_df: DataFrame with questions

        Returns:
            Path to generated markdown file
        """
        output_path = self.folder_path / "wrong_answers.md"

        # Load JSON logs for detailed information
        json_results = self.load_json_logs()

        # Analyze results
        extracted_cols = [col for col in solution_df.columns if col.startswith('prediction_')]
        results = []

        for idx, row in solution_df.iterrows():
            question_id = row['question_id']
            correct_answer = correct_df[correct_df['question_id'] == question_id]['answer'].values[0]

            result_row = {
                'question_id': question_id,
                'correct_answer': correct_answer
            }

            is_correct_list = []
            for extracted_col in extracted_cols:
                prediction = row[extracted_col]

                is_correct = are_answers_equal(prediction, correct_answer)
                result_row[extracted_col] = prediction
                result_row[f'{extracted_col}_is_correct'] = is_correct
                is_correct_list.append(is_correct)

            import numpy as np
            result_row['mean_correctness_rate'] = np.mean(is_correct_list)
            results.append(result_row)

        results_df = pd.DataFrame(results)
        results_df = results_df.sort_values(by=['mean_correctness_rate', 'question_id'], ascending=[True, True])

        wrong_questions = results_df[results_df['mean_correctness_rate'] < 1.0]
        completely_wrong = results_df[results_df['mean_correctness_rate'] == 0.0]
        partially_correct = results_df[(results_df['mean_correctness_rate'] > 0) & (results_df['mean_correctness_rate'] < 1.0)]

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# Wrong Answers Analysis Report\n\n")
            f.write(f"Total questions: {len(results_df)}\n")
            f.write(f"Questions with at least one wrong answer: {len(wrong_questions)}\n")
            f.write(f"Questions with all wrong answers: {len(completely_wrong)}\n")
            f.write(f"Questions with partially correct answers: {len(partially_correct)}\n\n")

            # Group by run instead of by question
            f.write("## Detailed Wrong Answers (Grouped by Run)\n\n")

            num_runs = len(extracted_cols)
            for run_idx in range(1, num_runs + 1):
                extracted_col = f'prediction_{run_idx}'
                is_correct_col = f'{extracted_col}_is_correct'

                # Find questions wrong in this run
                wrong_in_run = results_df[results_df[is_correct_col] == False]

                if len(wrong_in_run) == 0:
                    continue

                f.write(f"### Run {run_idx}\n\n")
                f.write(f"Questions with wrong answers: {len(wrong_in_run)}\n\n")

                for _, row in wrong_in_run.iterrows():
                    qid = row['question_id']
                    correct = row['correct_answer']
                    prediction = row[extracted_col]

                    # Get question from dataset
                    question_row = dataset_df[dataset_df['question_id'] == qid]
                    if question_row.empty:
                        f.write(f"#### Question {qid} - Prediction: {prediction} ✗ (Correct: {correct})\n\n")
                        f.write("**Question not found in dataset**\n\n")
                        continue

                    question_text = question_row['question'].iloc[0]
                    question_only, choices = parse_question_choices(question_text)

                    f.write(f"#### Question {qid} - Prediction: {prediction} ✗ (Correct: {correct})\n\n")
                    f.write(f"**Question:**\n{question_only}\n\n")

                    if choices:
                        f.write(f"**Choices:**\n")
                        for letter, choice_text in choices.items():
                            is_correct_choice = letter in normalize_answer(correct)
                            marker = "✓" if is_correct_choice else ""
                            f.write(f"- [{letter}] {choice_text} {marker}\n")
                        f.write("\n")

                    # Get raw response from JSON log
                    if qid in json_results and run_idx <= len(json_results[qid]):
                        json_entry = json_results[qid][run_idx - 1]
                        raw_response = json_entry.get('raw_response', '')
                        usage = json_entry.get('usage', {}) or {}

                        f.write(f"**LLM Response:**\n```\n{raw_response}\n```\n\n")
                        f.write(f"**Usage:**\n")
                        f.write(f"- Tokens: {usage.get('total_tokens', 'N/A')} ")
                        f.write(f"({usage.get('prompt_tokens', 0)} prompt + ")
                        f.write(f"{usage.get('completion_tokens', 0)} completion)\n")
                        f.write(f"- Cost: ${usage.get('cost', 0):.6f}\n\n")
                    else:
                        f.write("**Raw response not available in logs**\n\n")

                    f.write("---\n\n")

        return str(output_path)
