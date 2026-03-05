# Solution Analysis Report
Generated: 2026-03-01 13:33:07

## Configuration

### Model Parameters
- **Model**: qwen/qwen3.5-plus-02-15
- **Temperature**: 1.0
- **Max Tokens**: None
- **Max Reasoning Tokens**: 0

### Dataset
- **Test Dataset**: ../../train.csv
- **Solution File**: ../../train_solution.csv

### Execution
- **Number of Runs**: 5
- **Start Time**: 2026-03-01 13:31:57
- **End Time**: 2026-03-01 13:33:07
- **Duration**: 0:01:09.870817

### Message
Training dataset. Baseline. Zeroshot. Forcing no reasoning.

## Results Summary

- **Mean Accuracy**: 0.5837 ± 0.0208
- **Total Cost**: $0.0259
- **Total Tokens**: 56,557
  - Prompt Tokens: 54,895
  - Completion Tokens: 1,662
- **Total API Requests**: 245

## Performance per Run

| Run | Accuracy | Correct / Total | Cost ($) | Tokens (Prompt + Completion) |
|-----|----------|---------------|----------|-----------------------------|
| 1 | 0.5510 | 27 / 49 | $0.0052 | 11,312 (10,979 + 333) |
| 2 | 0.6122 | 30 / 49 | $0.0052 | 11,313 (10,979 + 334) |
| 3 | 0.5918 | 29 / 49 | $0.0052 | 11,306 (10,979 + 327) |
| 4 | 0.5714 | 28 / 49 | $0.0052 | 11,320 (10,979 + 341) |
| 5 | 0.5918 | 29 / 49 | $0.0052 | 11,306 (10,979 + 327) |

## Cost Efficiency Analysis

### Overall Metrics

- **Cost per 1% Accuracy**: $0.044454
- **Tokens per 1% Accuracy**: 96898.4
- **Average Cost per Question**: $0.000530
- **Average Tokens per Question**: 1154.2

### Average Per Run

- **Average Cost per Run**: $0.005189
- **Average Tokens per Run**: 11311.4
  - Prompt Tokens: 10979.0
  - Completion Tokens: 332.4
