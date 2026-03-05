# 🏆 LLM Reliability Benchmark System

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Kaggle Challenge](https://img.shields.io/badge/Kaggle-Data_Challenge-orange.svg)](https://www.kaggle.com/t/1b59fd489c784c558a981f68327644cf)

> This repository contains a framework to help you prepare the data challenge for the course Generative AI for Risk and Reliability in Centralesupelec, France. You will find:
- A framework to parallelize model testing
- A pipeline to help you run the test and generate the submission file

---

## 📖 Overview

This repository supports the **[Kaggle Data Challenge: LLM Reliability Benchmark](https://www.kaggle.com/t/1b59fd489c784c558a981f68327644cf)**, providing a robust framework for:

- ⚡ **Parallel Execution**: Accelerate experiments with concurrent model testing
- 📊 **Comprehensive Metrics**: Track accuracy, cost, tokens, and Kaggle scores
- 🎯 **Flexible Evaluation**: Custom evaluation scripts via `my_eval.py`
- 💰 **Cost-Aware Scoring**: Kaggle formula that rewards efficient models

## Allowed model lists
- "deepseek/deepseek-v3.2",
- "mistralai/mistral-large-2512",
- "qwen/qwen3-235b-a22b-2507",
- "openai/gpt-4.1-mini",
- "openai/gpt-5-mini",
- "google/gemini-3-flash-preview",
- "x-ai/grok-4.1-fast"
---

## 🚀 Quick Start

### 📦 Installation

```bash
# Clone the repository
git clone https://github.com/sonic160/scripts_gair_2026.git 

Or download all the source code directly from https://github.com/sonic160/scripts_gair_2026#

cd scripts_gair_2026

# Install dependencies
pip install pandas tqdm requests

# Set your OpenRouter API key
export OPENROUTER_API_KEY=your_key_here
```

---

## 📤 Prepare Submission File for the data challege 

To run the tests and generate a submission file, follow these steps:

### Step 1: Create Your Evaluation Script

All your custom logic **must** be implemented in a python script `my_eval.py`. This script must contain a `evaluate_question()` that answer each equestion and return the extracted answer. The system will call `evaluate_question()` for each question.

**Required Interface**:

```python
def evaluate_question(
    question: str,
    client,  # OpenRouterClient instance
    model: str,
    config: dict
) -> dict:
    """
    Evaluate a single question.

    Args:
        question: Question text from dataset
        client: OpenRouterClient for API calls
        model: Model identifier (e.g., "openai/gpt-4o-mini")
        config: Configuration dictionary

    Returns:
        {
            'raw_response': str,        # Complete LLM response (for debugging)
            'extracted_answer': str,    # Final answer (becomes prediction)
            'usage': dict,              # Per-question API usage metrics
            'metadata': dict            # Optional: additional info
        }
    """

    # Get usage summary before API call
    usage_before = client.get_usage_summary()

    # Your custom logic here
    # 1. Call LLM via client.chat_completion()
    # 2. Extract answer from response
    # 3. Return required fields: raw_response, and extracted_answer

    # Get usage summary after API call
    usage_after = client.get_usage_summary()
    # Calculate per-question usage as difference
    total_usage = {
        'cost': usage_after['cumulative_cost'] - usage_before['cumulative_cost'],
        'total_tokens': usage_after['total_tokens'] - usage_before['total_tokens'],
        'prompt_tokens': usage_after['total_prompt_tokens'] - usage_before['total_prompt_tokens'],
        'completion_tokens': usage_after['total_completion_tokens'] - usage_before['total_completion_tokens'],
        'reasoning_tokens': usage_after['total_reasoning_tokens'] - usage_before['total_reasoning_tokens'],
        'cached_tokens': usage_after['total_cached_tokens'] - usage_before['total_cached_tokens'],
        'request_count': usage_after['request_count'] - usage_before['request_count']
    }

    return {
        'raw_response': raw_response,
        'extracted_answer': extracted_answer,
        'usage': total_usage,
        'metadata': {
            'model': model,
            'finish_reason': response['choices'][0].get('finish_reason')
        }
    }
```

**You can use `scripts/my_eval.py` as a template.**

**📝 Answer Format Requirements**:
- Single-answer: `"a"` (case-insensitive)
- Multiple-answer: `"a, b, c"` (comma-separated, with a space after each comma)
- The system normalizes answers before comparison

### Step 2: Create Test Mode Config

Create a json file to define the test parameters, and put it under './configs/'. Each test you run will need a separate json file.

```json
{
  "models": ["google/gemini-3-flash-preview"],
  "results_path": "../experiments/my_submission",
  "dataset_path": "../experiments/test.csv",
  "solution_path": "",
  "eval_script_path": "./my_eval.py",
  "temperature": 1.0,
  "max_reasoning_tokens": 600,
  "max_tokens": null,
  "num_repetitions": 1,
  "testing_mode": true,
  "workers": 1,
  "enable_parallel": false,
  "max_workers_per_model": 1,
  "rate_limit_seconds": 1.0,
  "message": "Kaggle submission"
}
```

📁 Configuration Reference

| Parameter | Type | Description |
|-----------|------|-------------|
| `models` | `list[str]` | A list, containing the names of the models to evaluate. Example ['openai/gpt-4.1-mini'] |
| `results_path` | `str` | Output directory for results |
| `dataset_path` | `str` | Path to test data. If you use relative path, it has to be relative to `./script/` |
| `solution_path` | `str` | Path to ground truth (training only) |
| `eval_script_path` | `str` | Path to your script to define your code |
| `temperature` | `float` | LLM sampling temperature |
| `max_tokens` | `int?` | Max completion tokens |
| `max_reasoning_tokens` | `int?` | Max reasoning tokens. Set it to $0$ if you want to deactivate reasoning. |
| `num_repetitions` | `int` | Number of independent runs. Set to 5 for the data challenge |
| `testing_mode` | `bool` | Skip accuracy calc (for submission) |
| `workers` | `int` | Parallel models (≤ 10 / max_workers_per_model) |
| `enable_parallel` | `bool` | Enable parallel repetition execution |
| `max_workers_per_model` | `int` | Parallel reps per model |
| `rate_limit_seconds` | `float` | Delay between API calls (default: 1.0) |
| `message` | `str?` | Optional description for reports |

---


**🔑 Key Settings for Test Mode**:
- `"testing_mode": true` - Skips accuracy calculation (no ground truth)
- `"num_repetitions": 5` - five runs for submission
- `enable_parallel": faule` - Desabled parallel execution. If using parallization, set it to "true"
- `"workers": 1` - Start n process that runs in parallel. max 2.
- `"max_workers_per_model": 1` - Number of parallel runs per process. max 5.

### Step 3: Run Benchmark

```bash
cd scripts
python batch_test_models.py --config ./configs/testdata_generate_submission.json
```

This is a sample run of the benchmark. You need:
- create your own solution function based on `scripts/my_eval.py`
- create your own config file based on `configs/testdata_generate_submission.json`
- Run your own benchmark.

### Step 4: Locate Submission File

```
experiments/my_submission/
└── model-name_timestamp/
    ├── solution_kaggle.csv              # ✅ Submit this to Kaggle!
```

### An example

Below is a minimum example that used a pre-defined json to run a test using `qwen-235b-a22b-2507` model. You can use it as an example to create your own solution.

```bash
cd scripts/
python ./batch_test_models.py --config ./configs/testdata_generate_submission.json
```


## 🎯 Tuning Models on Training Dataset

Use the training dataset (`train.csv` + `train_solution.csv`) to evaluate and optimize your approach before submitting.

### Step 1: Create Training Config

Create `training_config.json`:

```json
{
  "models": ["google/gemini-3-flash-preview", "openai/gpt-4o-mini"],
  "results_path": "../experiments/my_training",
  "dataset_path": "../experiments/train.csv",
  "solution_path": "../experiments/train_solution.csv",
  "eval_script_path": "./my_eval.py",
  "temperature": 1.0,
  "max_reasoning_tokens": 600,
  "max_tokens": null,
  "num_repetitions": 5,
  "testing_mode": false,
  "workers": 2,
  "enable_parallel": true,
  "max_workers_per_model": 5,
  "rate_limit_seconds": 1.0,
  "message": "Training evaluation with ground truth"
}
```

**🔑 Key Settings for Training**:
- `"testing_mode": false` - Calculates accuracy using `train_solution.csv`
- `"num_repetitions": 5` - Multiple runs for statistical significance
- `"workers": 2` × `"max_workers_per_model": 5` = 10 concurrent requests ✅

### Step 2: Run Training Evaluation

```bash
cd scripts
python batch_test_models.py --config ./configs/training_data_cot.json
```

This script runs a benchmark using `./my_eval_cot.py`, which uses a "think-step-by-step" prompt and test on the selected model.


### Step 3: Analyze Results

The system generates comprehensive reports:

```
experiments/my_training/
├── model-name_1_timestamp/
│   ├── result_analysis.md           # ⭐ Accuracy, Kaggle score, cost
│   ├── wrong_answers.md             # Detailed error analysis
│   ├── run_1_results.json          # Raw responses per run
│   ├── run_2_results.json
│   └── ...
└── summary.md                       # ⭐ Model comparison table
```

**📊 Model Comparison** (`summary.md`):
```markdown
## Results Summary

| Rank | Model | Accuracy | Kaggle Score | Total Cost ($) | Avg Cost/Run ($) |
|------|-------|----------|--------------|----------------|------------------|
| 1 | google-gemini-3-flash-preview | 0.8693 ± 0.0131 | 0.8402 | $1.1487 | $0.230 |
| 2 | openai-gpt-4o-mini | 0.7867 ± 0.0223 | 0.7798 | $0.2279 | $0.046 |

```

### 🧪 Testing Your Evaluation Script

Before running full benchmarks, test your `my_eval.py` locally:

```bash
cd scripts
python my_eval.py
```

This runs a single test question and validates:
- ✅ Required fields are returned
- ✅ API calls work correctly
- ✅ Answer extraction functions properly

---


### 🏗️ Repository Structure

```
.
├── scripts/
│   ├── batch_test_models.py      # Main entry point for benchmarking
│   ├── my_eval.py                 # Template for your evaluation logic
│   └── configs/                   # Configuration examples
│       ├── training_data_zero_shot.json
│       └── test_scenario_*.json
├── supporting_scripts/
│   ├── openrouter_client.py       # API client with rate limiting
│   ├── benchmark_runner.py        # Orchestrates parallel execution
│   └── benchmark_logger.py        # Generates reports and metrics
└── experiments/                   # 📁 Example benchmark results
    ├── train.csv                  # Training dataset with ground truth
    ├── train_solution.csv         # Training labels
    ├── test.csv                   # Test dataset (no labels)
    ├── training_data_zero-shot/   # Benchmark results: zero-shot prompting
    ├── training_think-step-by-step/  # Benchmark results: chain-of-thought
    └── summary.md                 # Model comparison tables
```

**🔍 Example Results**: The `experiments/` folder contains benchmark results from various models and prompting strategies. These can help you understand expected performance levels and optimize your approach.

---

## ⚠️ Rate Limiting & Parallelization

This system includes **automatic rate limiting** and **parallel execution** to accelerate your experiments while respecting API constraints:

| Setting | Default | Description |
|---------|---------|-------------|
| **Rate Limit** | 1 request/second | Minimum delay between API calls |
| **Max Concurrent** | 10 instances | Maximum simultaneous API requests |

### 🚀 Parallel Execution

The system supports **two-level parallelism**:
- **Model-level**: Test multiple models simultaneously
- **Repetition-level**: Run multiple repetitions per model in parallel

**⚙️ Worker Configuration**:
```json
{
  "workers": 2,                    // Models to test in parallel
  "max_workers_per_model": 5,      // Repetitions per model in parallel
  "enable_parallel": true          // Enable parallel execution
}
```

**⚠️ Critical Constraint**:
```
workers × max_workers_per_model ≤ 10
```

✅ **Valid**: `workers=2` × `max_workers_per_model=5` = **10 concurrent requests**
❌ **Invalid**: `workers=3` × `max_workers_per_model=5` = **15 concurrent requests** (exceeds limit!)

---

## 🧮 Kaggle Scoring Formula

The competition uses a cost-aware scoring metric:

```
kaggle_score = max(0, min(1.0, accuracy - 0.15 × avg_cost_per_run))
```

**💡 Strategy Implications**:
- **Higher accuracy** → Better score
- **Lower cost** → Better score (0.15× cost penalty)
- **Sweet spot**: Balance quality vs. efficiency
- **Cost cap**: Scores drop to 0 if `avg_cost_per_run > 0.30`

---

## 🛠️ Advanced Features

### 🔄 Custom Evaluation Scripts

Modify `my_eval.py` to implement:
- Different prompting strategies (few-shot, chain-of-thought, etc.)
- Custom answer extraction logic
- Multi-step reasoning workflows
- Ensemble methods across multiple runs

### 📊 Usage Tracking

The system automatically tracks:
- **Cost**: Per-question and cumulative
- **Tokens**: Prompt, completion, reasoning, cached
- **Requests**: API call count
- **Performance metrics**: Accuracy, Kaggle score, timing

### 🎨 Parallelization Strategies

**Single Model, Multiple Repetitions** (Fast):
```json
{
  "models": ["google/gemini-3-flash-preview"],
  "num_repetitions": 10,
  "workers": 1,
  "max_workers_per_model": 10
}
```

**Multiple Models, Single Repetition** (Comparison):
```json
{
  "models": ["model1", "model2", "model3"],
  "num_repetitions": 1,
  "workers": 3,
  "max_workers_per_model": 1
}
```

---

## 🤝 Contributing

This is part of the **LLM Reliability Engineering** project. Contributions welcome!

---

## 📄 License

Part of LLM Reliability Engineering project.

---

## 🙏 Acknowledgments

- Built for the [Kaggle Data Challenge](https://www.kaggle.com/t/1b59fd489c784c558a981f68327644cf)
- Uses [OpenRouter API](https://openrouter.ai/) for multi-model access
- Implements cost-aware evaluation inspired by real-world LLM deployment constraints
