# Solution Analysis Report
Generated: 2026-03-01 13:28:43

## Configuration

### Model Parameters
- **Model**: google/gemini-3-flash-preview
- **Temperature**: 1.0
- **Max Tokens**: None
- **Max Reasoning Tokens**: 0

### Dataset
- **Test Dataset**: ../../train.csv
- **Solution File**: ../../train_solution.csv

### Execution
- **Number of Runs**: 5
- **Start Time**: 2026-03-01 13:27:46
- **End Time**: 2026-03-01 13:28:43
- **Duration**: 0:00:56.317216

### Message
Training dataset. Baseline. Zeroshot. Forcing no reasoning.

## Results Summary

- **Mean Accuracy**: 0.6776 ± 0.0396
- **Total Cost**: $0.0304
- **Total Tokens**: 52,716
  - Prompt Tokens: 51,081
  - Completion Tokens: 1,635
- **Total API Requests**: 245

## Performance per Run

| Run | Accuracy | Correct / Total | Cost ($) | Tokens (Prompt + Completion) |
|-----|----------|---------------|----------|-----------------------------|
| 1 | 0.6327 | 31 / 49 | $0.0060 | 10,514 (10,211 + 303) |
| 2 | 0.7347 | 36 / 49 | $0.0061 | 10,535 (10,211 + 324) |
| 3 | 0.6531 | 32 / 49 | $0.0061 | 10,558 (10,213 + 345) |
| 4 | 0.7143 | 35 / 49 | $0.0061 | 10,535 (10,217 + 318) |
| 5 | 0.6531 | 32 / 49 | $0.0061 | 10,574 (10,229 + 345) |

## Cost Efficiency Analysis

### Overall Metrics

- **Cost per 1% Accuracy**: $0.044935
- **Tokens per 1% Accuracy**: 77803.7
- **Average Cost per Question**: $0.000621
- **Average Tokens per Question**: 1075.8

### Average Per Run

- **Average Cost per Run**: $0.006089
- **Average Tokens per Run**: 10543.2
  - Prompt Tokens: 10216.2
  - Completion Tokens: 327.0
