#!/usr/bin/env python3
"""
Create summary report from multiple model result_analysis.md files.

Scans all subfolders for result_analysis.md files and generates a comparison report
similar to batch_test_models.py output.

Usage:
    python create_summary_report.py [path] [options]

Example:
    python create_summary_report.py ../experiments/training_data_zero-shot
    python create_summary_report.py . --output custom_summary
"""
import argparse
import re
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import csv
import pandas as pd


def are_answers_equal(pred: str, correct: str) -> bool:
    """Check if predicted answer matches correct answer.
    
    Handles comma-separated multiple answers like "a, b, c".
    Uses same logic as benchmark_logger.py for consistency.
    
    Args:
        pred: Predicted answer string
        correct: Correct answer string
    
    Returns:
        True if answers match, False otherwise
    """
    def normalize_answer(answer):
        if pd.isna(answer) or answer == "":
            return ""
        return str(answer).strip().lower().replace(", ", ",")
    
    pred_norm = normalize_answer(pred)
    correct_norm = normalize_answer(correct)
    
    pred_set = set(p.strip() for p in pred_norm.split(',') if p.strip())
    correct_set = set(c.strip() for c in correct_norm.split(',') if c.strip())
    
    return pred_set == correct_set


def create_per_question_table(
    solution_csv_path: Path,
    correct_solution_path: Path,
    num_repetitions: int
) -> str:
    """Generate per-question results table as markdown string.
    
    Args:
        solution_csv_path: Path to solution.csv with predictions
        correct_solution_path: Path to correct solution file with ground truth
        num_repetitions: Number of experimental runs
    
    Returns:
        Markdown string with per-question results table, or empty string if error
    """
    try:
        solution_df = pd.read_csv(solution_csv_path)
        correct_df = pd.read_csv(correct_solution_path)
        
        question_results = []
        
        for _, row in solution_df.iterrows():
            qid = row['question_id']
            predictions = []
            correct_count = 0
            
            for run_idx in range(1, num_repetitions + 1):
                pred_col = f'prediction_{run_idx}'
                pred = row.get(pred_col, '')
                predictions.append(str(pred).strip() if pred else '')
            
            correct_row = correct_df[correct_df['question_id'] == qid]
            if correct_row.empty:
                continue
            
            correct_answer = correct_row['answer'].values[0]
            
            for pred in predictions:
                if pred and are_answers_equal(pred, correct_answer):
                    correct_count += 1
            
            accuracy = correct_count / num_repetitions
            
            question_results.append({
                'question_id': qid,
                'predictions': predictions,
                'correct_answer': correct_answer,
                'accuracy': accuracy
            })
        
        question_results.sort(key=lambda x: x['accuracy'])
        
        if not question_results:
            return ""
        
        pred_columns = [f'Prediction_{i}' for i in range(1, num_repetitions + 1)]
        header = "| Question ID | " + " | ".join(pred_columns) + " | Correct Answer | Accuracy |\n"
        separator = "|-------------|" + "|".join(["--------------" for _ in range(num_repetitions)]) + "|----------------|----------|\n"
        
        lines = [header, separator]
        
        for qr in question_results:
            qid_str = str(qr['question_id'])
            preds_str = " | ".join([str(p) if p else '' for p in qr['predictions']])
            correct_str = str(qr['correct_answer'])
            acc_str = f"{qr['accuracy']:.2f}"
            
            line = f"| {qid_str} | {preds_str} | {correct_str} | {acc_str} |\n"
            lines.append(line)
        
        return "".join(lines)
        
    except Exception as e:
        print(f"  Warning: Failed to create per-question table: {e}")
        return ""


def insert_section_after(
    md_path: Path,
    after_section: str,
    section_title: str,
    section_content: str
) -> bool:
    """Insert a new section into markdown file after a specific section.
    
    Args:
        md_path: Path to markdown file
        after_section: Section header after which to insert (e.g., "## Performance per Run")
        section_title: Title for new section (e.g., "## Per-question results")
        section_content: Content to insert (should not include the title)
    
    Returns:
        True if successful, False otherwise
    """
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        insert_idx = None
        for i, line in enumerate(lines):
            if line.strip() == after_section:
                insert_idx = i + 1
                break
        
        if insert_idx is None:
            return False
        
        while insert_idx < len(lines) and not lines[insert_idx].strip().startswith('##'):
            insert_idx += 1
        
        new_lines = [f"{section_title}\n", section_content, "\n"]
        lines[insert_idx:insert_idx] = new_lines
        
        with open(md_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        return True
        
    except Exception as e:
        print(f"  Warning: Failed to insert section into {md_path.name}: {e}")
        return False


def extract_field(lines: List[str], pattern: str, default: str = "") -> str:
    """
    Extract a field value from lines using regex pattern.

    Args:
        lines: List of strings to search
        pattern: Regex pattern with one capture group
        default: Default value if not found

    Returns:
        Extracted value or default
    """
    for line in lines:
        match = re.search(pattern, line)
        if match:
            return match.group(1).strip()
    return default


def parse_result_analysis(md_path: Path) -> Optional[Dict]:
    """
    Parse result_analysis.md and extract key metrics.

    Args:
        md_path: Path to result_analysis.md file

    Returns:
        Dictionary with extracted metrics or None if parsing fails
    """
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Extract model name (from folder name since we're using original names)
        model = md_path.parent.name

        # Extract metrics from result_analysis.md
        mean_acc_line = extract_field(lines, r'- \*\*Mean Accuracy\*\*:\s*([\d\.N/A±\s]+)')
        kaggle_score_line = extract_field(lines, r'- \*\*Mean Kaggle Score\*\*:\s*([\d\.N/A±\s]+)')
        total_cost = extract_field(lines, r'- \*\*Total Cost\*\*:\s*\$?([\d\.]+)').replace('$', '')
        total_tokens = extract_field(lines, r'- \*\*Total Tokens\*\*:\s*([\d,]+)').replace(',', '')
        avg_cost_run = extract_field(lines, r'- \*\*Average Cost per Run\*\*:\s*\$?([\d\.]+)').replace('$', '')
        avg_tokens_run = extract_field(lines, r'- \*\*Average Tokens per Run\*\*:\s*([\d\.]+)')
        cost_per_pct = extract_field(lines, r'- \*\*Average cost per 1% Accuracy \(dollar cents\)\*\*:\s*\$?([\d\.]+)').replace('$', '')
        duration = extract_field(lines, r'- \*\*Duration\*\*:\s*([\d:\.]+)')
        temperature = extract_field(lines, r'- \*\*Temperature\*\*:\s*([\d\.]+)')
        max_reasoning = extract_field(lines, r'- \*\*Max Reasoning Tokens\*\*:\s*([\dNone]+)')
        num_runs = extract_field(lines, r'- \*\*Number of Runs\*\*:\s*(\d+)')
        dataset = extract_field(lines, r'- \*\*Test Dataset\*\*:\s*(.+)$')
        message = extract_field(lines, r'Test dataset\.\s+(.+)', "")

        # Parse accuracy: "0.7333 ± 0.0146" -> mean=0.7333, std=0.0146
        mean_acc = None
        std_acc = None
        if mean_acc_line and '±' in mean_acc_line:
            parts = mean_acc_line.split('±')
            mean_acc = float(parts[0].strip())
            std_acc = float(parts[1].strip())
        elif mean_acc_line and mean_acc_line != 'N/A':
            mean_acc = float(mean_acc_line)

        # Parse Kaggle score: "0.6234" -> mean=0.6234 (no std)
        mean_kaggle = None
        if kaggle_score_line and '±' in kaggle_score_line:
            # Handle legacy format with ± - extract only mean
            parts = kaggle_score_line.split('±')
            mean_kaggle = float(parts[0].strip())
        elif kaggle_score_line and kaggle_score_line != 'N/A':
            mean_kaggle = float(kaggle_score_line)

        # Convert to numeric types
        total_cost = float(total_cost) if total_cost else 0.0
        total_tokens = int(total_tokens) if total_tokens else 0
        avg_cost_run = float(avg_cost_run) if avg_cost_run else 0.0
        avg_tokens_run = float(avg_tokens_run) if avg_tokens_run else 0.0
        cost_per_pct = float(cost_per_pct) if cost_per_pct else 0.0
        temperature = float(temperature) if temperature else 1.0
        num_runs = int(num_runs) if num_runs else 5
        
        # If avg_cost_per_run is not available, calculate it from total_cost / num_runs
        if avg_cost_run == 0.0 and total_cost > 0 and num_runs > 0:
            avg_cost_run = total_cost / num_runs

        return {
            'model': model,
            'mean_accuracy': mean_acc,
            'std_accuracy': std_acc,
            'mean_kaggle_score': mean_kaggle,
            'total_cost': total_cost,
            'total_tokens': total_tokens,
            'avg_cost_per_run': avg_cost_run,
            'avg_tokens_per_run': avg_tokens_run,
            'cost_per_1pct_accuracy': cost_per_pct,
            'duration': duration,
            'temperature': temperature,
            'max_reasoning_tokens': max_reasoning,
            'num_repetitions': num_runs,
            'dataset': dataset,
            'message': message
        }
    except Exception as e:
        print(f"Warning: Failed to parse {md_path}: {e}")
        return None


def create_solution_kaggle_csv(subfolder_path: Path, avg_cost_per_run: float) -> bool:
    """
    Create solution_kaggle.csv by copying solution.csv and adding 'Average cost per run' column.
    Replaces any NaN values with 'no solution or nan generated'.
    
    Args:
        subfolder_path: Path to the model subfolder
        avg_cost_per_run: Average cost per run value to add as column
    
    Returns:
        True if successful, False otherwise
    """
    solution_csv = subfolder_path / 'solution.csv'
    kaggle_csv = subfolder_path / 'solution_kaggle.csv'
    
    # Check if solution.csv exists
    if not solution_csv.exists():
        return False
    
    try:
        # Read solution.csv
        with open(solution_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            fieldnames = reader.fieldnames
        
        # Add new column
        new_fieldnames = fieldnames + ['Average cost per run']
        
        # Write solution_kaggle.csv with new column
        with open(kaggle_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=new_fieldnames)
            writer.writeheader()
            
            for row in rows:
                # Check for NaN or empty values in prediction columns and replace them
                for key, value in row.items():
                    # Check if value is NaN-like (empty, 'nan', 'NaN', etc.)
                    if value == '' or value is None or (isinstance(value, str) and value.strip().lower() in ('nan', 'none', 'null')):
                        row[key] = 'no solution or nan generated'
                
                row['Average cost per run'] = f"{avg_cost_per_run:.6f}"
                writer.writerow(row)
        
        return True
    except Exception as e:
        print(f"  Warning: Failed to create solution_kaggle.csv for {subfolder_path.name}: {e}")
        return False


def add_per_question_results(subfolder: Path) -> bool:
    """Add per-question results table to result_analysis.md.
    
    Reads solution.csv and correct solution file, calculates per-question accuracy,
    and inserts a new section into result_analysis.md after "Performance per run".
    
    Args:
        subfolder: Path to model subfolder containing result_analysis.md
    
    Returns:
        True if successful, False otherwise
    """
    try:
        result_file = subfolder / 'result_analysis.md'
        if not result_file.exists():
            return False
        
        # Check if Per-question results section already exists
        with open(result_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if '## Per-question results' in content:
                return False  # Section already exists, skip
        
        with open(result_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        solution_file = extract_field(lines, r'- \*\*Solution File\*\*:\s*(.+)$')
        if not solution_file or solution_file == "N/A":
            return False
        
        num_runs = extract_field(lines, r'- \*\*Number of Runs\*\*:\s*(\d+)')
        if not num_runs:
            return False
        num_runs = int(num_runs)
        
        solution_csv = subfolder / 'solution.csv'
        if not solution_csv.exists():
            return False
        
        solution_path = Path(solution_file)
        if not solution_path.exists():
            return False
        
        table_content = create_per_question_table(solution_csv, solution_path, num_runs)
        if not table_content:
            return False
        
        section_title = "## Per-question results"
        
        if insert_section_after(result_file, "## Performance per Run", section_title, table_content):
            return True
        
        return False
        
    except Exception as e:
        print(f"  Warning: Could not add per-question results to {subfolder.name}: {e}")
        return False


def scan_directory(base_path: Path) -> List[Dict]:
    """
    Scan directory for result_analysis.md files and parse them.

    Args:
        base_path: Directory to scan

    Returns:
        List of parsed result dictionaries
    """
    results = []
    missing_count = 0

    print(f"Scanning {base_path} for result_analysis.md files...")

    for subfolder in base_path.iterdir():
        if not subfolder.is_dir():
            continue

        # Skip common non-model folders
        if subfolder.name in ['__pycache__', '.git']:
            continue

        result_file = subfolder / 'result_analysis.md'
        if not result_file.exists():
            missing_count += 1
            print(f"  [SKIP] {subfolder.name}: No result_analysis.md found")
            continue

        parsed = parse_result_analysis(result_file)
        if parsed:
            results.append(parsed)
            print(f"  [OK] {subfolder.name}: Accuracy={parsed['mean_accuracy']:.4f}" if parsed['mean_accuracy'] else f"  [OK] {subfolder.name}: Accuracy=N/A")
            
            # Create solution_kaggle.csv with average cost per run
            if create_solution_kaggle_csv(subfolder, parsed['avg_cost_per_run']):
                print(f"      [Created] solution_kaggle.csv (avg_cost_per_run=${parsed['avg_cost_per_run']:.6f})")
            else:
                print(f"      [Skip] No solution.csv found")
            
            # Add per-question results table to result_analysis.md
            try:
                if add_per_question_results(subfolder):
                    print(f"      [Added] Per-question results table")
            except Exception as e:
                pass

    if missing_count > 0:
        print(f"\nWarning: Skipped {missing_count} folders without result_analysis.md")

    return results


def generate_summary_markdown(results: List[Dict], output_path: Path, base_path: Path):
    """
    Generate summary.md markdown file.

    Args:
        results: List of parsed result dictionaries
        output_path: Path to output summary.md
        base_path: Base directory path (for metadata)
    """
    if not results:
        print("No results to write")
        return

    # Sort by accuracy descending
    results_sorted = sorted(results, key=lambda x: x['mean_accuracy'] or 0, reverse=True)

    # Extract common metadata from first result
    first = results_sorted[0]
    num_repetitions = first['num_repetitions']
    temperature = first['temperature']
    max_reasoning_tokens = first['max_reasoning_tokens']
    dataset = first['dataset']
    message = first['message'] or "Batch comparison"

    lines = []
    lines.append("# Model Comparison Report\n")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

    lines.append("## Configuration\n\n")
    lines.append(f"- **Models Tested**: {len(results)}\n")
    lines.append(f"- **Repetitions**: {num_repetitions}\n")
    lines.append(f"- **Temperature**: {temperature}\n")
    lines.append(f"- **Max Reasoning Tokens**: {max_reasoning_tokens}\n")
    lines.append(f"- **Dataset**: {dataset}\n")
    if message:
        lines.append(f"- **Message**: {message}\n")
    lines.append("\n")

    # Results Summary table
    lines.append("## Results Summary\n\n")
    lines.append("| Rank | Model | Accuracy | Kaggle Score | Total Cost ($) | Total Tokens | Avg Cost/Run ($) | Avg Tokens/Run | Cost per 1% Acc ($) | Duration |\n")
    lines.append("|------|-------|----------|--------------|----------------|--------------|------------------|----------------|---------------------|----------|\n")

    for idx, r in enumerate(results_sorted, 1):
        acc_str = f"{r['mean_accuracy']:.4f}" if r['mean_accuracy'] else "N/A"
        std_str = f" ± {r['std_accuracy']:.4f}" if r['std_accuracy'] else ""
        kaggle_str = f"{r['mean_kaggle_score']:.4f}" if r['mean_kaggle_score'] is not None else "N/A"
        cost_str = f"${r['total_cost']:.4f}" if r['total_cost'] else "N/A"
        tokens_str = f"{r['total_tokens']:,}" if r['total_tokens'] else "N/A"
        avg_cost_str = f"${r['avg_cost_per_run']:.6f}" if r['avg_cost_per_run'] else "N/A"
        avg_tokens_str = f"{r['avg_tokens_per_run']:.1f}" if r['avg_tokens_per_run'] else "N/A"
        cost_pct_str = f"${r['cost_per_1pct_accuracy']:.4f}" if r['cost_per_1pct_accuracy'] else "N/A"
        duration_str = f"{r['duration']}s" if r['duration'] else "N/A"

        lines.append(f"| {idx} | {r['model']} | {acc_str}{std_str} | {kaggle_str} | {cost_str} | {tokens_str} | {avg_cost_str} | {avg_tokens_str} | {cost_pct_str} | {duration_str} |\n")

    with open(output_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    print(f"\nGenerated: {output_path}")


def calculate_kaggle_score_manually(model_folder: Path, avg_cost_per_run: float, solution_path: Path) -> Optional[float]:
    """
    Calculate Kaggle score for old experiments without Kaggle score in result_analysis.md.

    Args:
        model_folder: Path to model folder containing solution.csv
        avg_cost_per_run: Average cost per run from result_analysis.md
        solution_path: Path to correct solution file

    Returns:
        Kaggle score or None if calculation fails
    """
    try:
        import pandas as pd
        import importlib.util
        from pathlib import Path as PathImport
        
        # Load eval_code module using importlib
        _eval_code_file = PathImport(__file__).parent / 'test_eval_code' / 'eval_code.py'
        spec = importlib.util.spec_from_file_location("eval_code", _eval_code_file)
        module = importlib.util.module_from_spec(spec)
        import sys as sys_module
        sys_module.modules["eval_code_manual"] = module
        spec.loader.exec_module(module)
        
        score_func = module.score

        solution_csv = model_folder / 'solution.csv'
        if not solution_csv.exists():
            return None

        # Create submission DataFrame with cost column
        submission_df = pd.read_csv(solution_csv)
        submission_df['Average cost per run'] = avg_cost_per_run

        # Read correct solution
        correct_df = pd.read_csv(solution_path)

        # Calculate Kaggle score
        kaggle_score = score_func(correct_df, submission_df, 'question_id')
        return kaggle_score

    except Exception as e:
        print(f"  Warning: Failed to calculate Kaggle score manually: {e}")
        return None


def main():
    """Main execution."""
    parser = argparse.ArgumentParser(
        description='Create summary report from multiple model result_analysis.md files'
    )
    parser.add_argument(
        'path',
        type=str,
        nargs='?',
        default='.',
        help='Path to directory containing model subfolders (default: current directory)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='summary',
        help='Output filename without extension (default: summary)'
    )
    parser.add_argument(
        '--solution-path',
        type=str,
        default=None,
        help='Path to solution.csv for calculating Kaggle scores in old experiments (default: None)'
    )

    args = parser.parse_args()

    # Resolve path
    base_path = Path(args.path).resolve()
    if not base_path.exists():
        print(f"Error: Path not found: {base_path}")
        sys.exit(1)

    if not base_path.is_dir():
        print(f"Error: Path is not a directory: {base_path}")
        sys.exit(1)

    print("=" * 80)
    print("CREATE SUMMARY REPORT")
    print("=" * 80)
    print(f"Base path: {base_path}")
    print("=" * 80 + "\n")

    # Scan directory and parse results
    results = scan_directory(base_path)

    if not results:
        print("\nNo result_analysis.md files found. Exiting.")
        sys.exit(1)

    print(f"\nFound {len(results)} valid result files")

    # Handle backward compatibility: calculate Kaggle score manually if missing
    if args.solution_path:
        solution_path = Path(args.solution_path).resolve()
        if not solution_path.exists():
            print(f"Warning: Solution path not found: {solution_path}")
        else:
            print(f"\nCalculating Kaggle scores for old experiments...")
            for result in results:
                if result.get('mean_kaggle_score') is None and result.get('mean_accuracy') is not None:
                    model_folder = base_path / result['model']
                    kaggle_score = calculate_kaggle_score_manually(
                        model_folder,
                        result['avg_cost_per_run'],
                        solution_path
                    )
                    if kaggle_score is not None:
                        result['mean_kaggle_score'] = kaggle_score
                        print(f"  [OK] {result['model']}: Kaggle={kaggle_score:.4f}")
                    else:
                        print(f"  [SKIP] {result['model']}: Could not calculate Kaggle score")

    # Generate outputs
    summary_md_path = base_path / f"{args.output}.md"
    generate_summary_markdown(results, summary_md_path, base_path)

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Models analyzed: {len(results)}")
    print(f"Best accuracy: {results[0]['mean_accuracy']:.4f}" if results[0]['mean_accuracy'] else "N/A")
    print(f"Generated {len(results)} solution_kaggle.csv files")
    print("=" * 80 + "\n")


if __name__ == '__main__':
    main()
