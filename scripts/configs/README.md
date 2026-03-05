# Batch Test Configuration Files

This directory contains JSON configuration files for `batch_test_models.py`.

## Available Configurations

### training_data_zero_shot.json
- **Models**: 11 models (full model suite)
- **Dataset**: Training data (train.csv)
- **Repetitions**: 5
- **Reasoning tokens**: 600
- **Workers**: 2 (model-level parallelism)
- **Parallel per model**: 3 workers
- **Purpose**: Full training data evaluation with reasoning allowed

### test_scenario_1.json
- **Models**: 1 model (google/gemini-3-flash-preview only)
- **Dataset**: Test data (3 questions)
- **Repetitions**: 2
- **Reasoning tokens**: 300
- **Workers**: 1 (sequential)
- **Parallel per model**: Disabled
- **Purpose**: Quick single-model test scenario

### test_scenario_3.json
- **Models**: 3 models (gpt-4.1-mini, gpt-5-mini, gemini-3-flash-preview)
- **Dataset**: Test data (3 questions)
- **Repetitions**: 5
- **Reasoning tokens**: 200
- **Workers**: 2 (model-level parallelism)
- **Parallel per model**: 5 workers
- **Purpose**: Multi-model parallel test scenario

## Usage

### Option 1: Use default config (set in batch_test_models.py)
```bash
python batch_test_models.py
```

### Option 2: Specify config via CLI
```bash
python batch_test_models.py --config configs/test_scenario_1.json
python batch_test_models.py --config configs/training_data_zero_shot.json
```

## Configuration Schema

```json
{
  "models": ["model/id1", "model/id2"],        // List of model IDs to test
  "results_path": "../path/to/results",         // Relative to scripts/
  "dataset_path": "../path/to/dataset.csv",     // Relative to scripts/
  "solution_path": "../path/to/solution.csv",   // Relative to scripts/
  "eval_script_path": "./my_eval.py",           // Relative to scripts/
  "temperature": 1.0,                           // LLM temperature
  "max_reasoning_tokens": 600,                  // Max reasoning tokens (0 = no reasoning)
  "max_tokens": null,                           // Max response tokens (null = model default)
  "num_repetitions": 5,                         // Number of test repetitions
  "testing_mode": false,                        // If true, skip accuracy calculation
  "workers": 2,                                 // Number of models to test in parallel
  "message": "Description of test",              // Message for report
  "enable_parallel": true,                      // Enable parallel execution per model
  "max_workers_per_model": 3,                   // Max parallel workers per model
  "rate_limit_seconds": 1.0                     // Rate limit between API calls
}
```

## Creating Custom Configs

To create a custom configuration:

1. Copy an existing config file:
   ```bash
   cp configs/training_data_zero_shot.json configs/my_config.json
   ```

2. Edit the values as needed

3. Run with your config:
   ```bash
   python batch_test_models.py --config configs/my_config.json
   ```
