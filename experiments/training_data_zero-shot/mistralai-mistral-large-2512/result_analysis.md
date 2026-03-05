# Solution Analysis Report
Generated: 2026-03-01 15:03:28

## Configuration

### Model Parameters
- **Model**: mistralai/mistral-large-2512
- **Temperature**: 1.0
- **Max Tokens**: None
- **Max Reasoning Tokens**: 600

### Dataset
- **Test Dataset**: ../../train.csv
- **Solution File**: ../../train_solution.csv

### Execution
- **Number of Runs**: 5
- **Start Time**: 2026-03-01 15:01:53
- **End Time**: 2026-03-01 15:03:28
- **Duration**: 0:01:34.709864

### Message
Training dataset. Baseline. Zeroshot. Allow reasonig for reasoning model.

## Results Summary

- **Mean Accuracy**: 0.5592 ± 0.0245
- **Total Cost**: $0.0312
- **Total Tokens**: 55,698
  - Prompt Tokens: 52,305
  - Completion Tokens: 3,393
- **Total API Requests**: 245

## Performance per Run

| Run | Accuracy | Correct / Total | Cost ($) | Tokens (Prompt + Completion) |
|-----|----------|---------------|----------|-----------------------------|
| 1 | 0.5918 | 29 / 49 | $0.0062 | 11,132 (10,461 + 671) |
| 2 | 0.5714 | 28 / 49 | $0.0062 | 11,136 (10,461 + 675) |
| 3 | 0.5306 | 26 / 49 | $0.0063 | 11,142 (10,461 + 681) |
| 4 | 0.5714 | 28 / 49 | $0.0063 | 11,143 (10,461 + 682) |
| 5 | 0.5306 | 26 / 49 | $0.0063 | 11,145 (10,461 + 684) |

## Cost Efficiency Analysis

### Overall Metrics

- **Cost per 1% Accuracy**: $0.055871
- **Tokens per 1% Accuracy**: 99605.9
- **Average Cost per Question**: $0.000638
- **Average Tokens per Question**: 1136.7

### Average Per Run

- **Average Cost per Run**: $0.006248
- **Average Tokens per Run**: 11139.6
  - Prompt Tokens: 10461.0
  - Completion Tokens: 678.6
