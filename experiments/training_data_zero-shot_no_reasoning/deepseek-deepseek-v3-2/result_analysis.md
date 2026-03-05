# Solution Analysis Report
Generated: 2026-03-01 13:31:01

## Configuration

### Model Parameters
- **Model**: deepseek/deepseek-v3.2
- **Temperature**: 1.0
- **Max Tokens**: None
- **Max Reasoning Tokens**: 0

### Dataset
- **Test Dataset**: ../../train.csv
- **Solution File**: ../../train_solution.csv

### Execution
- **Number of Runs**: 5
- **Start Time**: 2026-03-01 13:28:43
- **End Time**: 2026-03-01 13:31:01
- **Duration**: 0:02:18.396422

### Message
Training dataset. Baseline. Zeroshot. Forcing no reasoning.

## Results Summary

- **Mean Accuracy**: 0.5265 ± 0.0396
- **Total Cost**: $0.0138
- **Total Tokens**: 52,740
  - Prompt Tokens: 50,720
  - Completion Tokens: 2,020
- **Total API Requests**: 245

## Performance per Run

| Run | Accuracy | Correct / Total | Cost ($) | Tokens (Prompt + Completion) |
|-----|----------|---------------|----------|-----------------------------|
| 1 | 0.5714 | 28 / 49 | $0.0029 | 10,535 (10,144 + 391) |
| 2 | 0.5102 | 25 / 49 | $0.0027 | 10,545 (10,144 + 401) |
| 3 | 0.4694 | 23 / 49 | $0.0027 | 10,548 (10,144 + 404) |
| 4 | 0.5102 | 25 / 49 | $0.0028 | 10,559 (10,144 + 415) |
| 5 | 0.5714 | 28 / 49 | $0.0027 | 10,553 (10,144 + 409) |

## Cost Efficiency Analysis

### Overall Metrics

- **Cost per 1% Accuracy**: $0.026137
- **Tokens per 1% Accuracy**: 100165.1
- **Average Cost per Question**: $0.000281
- **Average Tokens per Question**: 1076.3

### Average Per Run

- **Average Cost per Run**: $0.002752
- **Average Tokens per Run**: 10548.0
  - Prompt Tokens: 10144.0
  - Completion Tokens: 404.0
