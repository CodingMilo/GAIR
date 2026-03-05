# Solution Analysis Report
Generated: 2026-03-01 17:07:10

## Configuration

### Model Parameters
- **Model**: qwen/qwen3-235b-a22b-2507
- **Temperature**: 1.0
- **Max Tokens**: None
- **Max Reasoning Tokens**: 600

### Dataset
- **Test Dataset**: ../../train.csv
- **Solution File**: ../../train_solution.csv

### Execution
- **Number of Runs**: 5
- **Start Time**: 2026-03-01 17:04:54
- **End Time**: 2026-03-01 17:07:10
- **Duration**: 0:02:15.599097

### Message
Training dataset. Baseline. Zeroshot. Allow reasonig for reasoning model.

## Results Summary

- **Mean Accuracy**: 0.6041 ± 0.0208
- **Total Cost**: $0.0071
- **Total Tokens**: 54,661
  - Prompt Tokens: 52,845
  - Completion Tokens: 1,816
- **Total API Requests**: 245

## Performance per Run

| Run | Accuracy | Correct / Total | Cost ($) | Tokens (Prompt + Completion) |
|-----|----------|---------------|----------|-----------------------------|
| 1 | 0.6122 | 30 / 49 | $0.0014 | 10,933 (10,569 + 364) |
| 2 | 0.5714 | 28 / 49 | $0.0014 | 10,936 (10,569 + 367) |
| 3 | 0.6122 | 30 / 49 | $0.0014 | 10,935 (10,569 + 366) |
| 4 | 0.6327 | 31 / 49 | $0.0014 | 10,934 (10,569 + 365) |
| 5 | 0.5918 | 29 / 49 | $0.0015 | 10,923 (10,569 + 354) |

## Cost Efficiency Analysis

### Overall Metrics

- **Cost per 1% Accuracy**: $0.011777
- **Tokens per 1% Accuracy**: 90486.1
- **Average Cost per Question**: $0.000145
- **Average Tokens per Question**: 1115.5

### Average Per Run

- **Average Cost per Run**: $0.001423
- **Average Tokens per Run**: 10932.2
  - Prompt Tokens: 10569.0
  - Completion Tokens: 363.2
