# Solution Analysis Report
Generated: 2026-03-01 13:27:40

## Configuration

### Model Parameters
- **Model**: openai/gpt-4.1-mini
- **Temperature**: 1.0
- **Max Tokens**: None
- **Max Reasoning Tokens**: 0

### Dataset
- **Test Dataset**: ../../train.csv
- **Solution File**: ../../train_solution.csv

### Execution
- **Number of Runs**: 5
- **Start Time**: 2026-03-01 13:26:56
- **End Time**: 2026-03-01 13:27:40
- **Duration**: 0:00:44.516851

### Message
Training dataset. Baseline. Zeroshot. Forcing no reasoning.

## Results Summary

- **Mean Accuracy**: 0.4490 ± 0.0387
- **Total Cost**: $0.0239
- **Total Tokens**: 53,413
  - Prompt Tokens: 51,300
  - Completion Tokens: 2,113
- **Total API Requests**: 245

## Performance per Run

| Run | Accuracy | Correct / Total | Cost ($) | Tokens (Prompt + Completion) |
|-----|----------|---------------|----------|-----------------------------|
| 1 | 0.4694 | 23 / 49 | $0.0048 | 10,682 (10,260 + 422) |
| 2 | 0.4082 | 20 / 49 | $0.0048 | 10,685 (10,260 + 425) |
| 3 | 0.4082 | 20 / 49 | $0.0048 | 10,682 (10,260 + 422) |
| 4 | 0.5102 | 25 / 49 | $0.0048 | 10,682 (10,260 + 422) |
| 5 | 0.4490 | 22 / 49 | $0.0048 | 10,682 (10,260 + 422) |

## Cost Efficiency Analysis

### Overall Metrics

- **Cost per 1% Accuracy**: $0.053234
- **Tokens per 1% Accuracy**: 118965.3
- **Average Cost per Question**: $0.000488
- **Average Tokens per Question**: 1090.1

### Average Per Run

- **Average Cost per Run**: $0.004780
- **Average Tokens per Run**: 10682.6
  - Prompt Tokens: 10260.0
  - Completion Tokens: 422.6
