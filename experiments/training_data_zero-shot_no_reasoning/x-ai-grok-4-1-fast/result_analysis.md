# Solution Analysis Report
Generated: 2026-03-01 13:31:51

## Configuration

### Model Parameters
- **Model**: x-ai/grok-4.1-fast
- **Temperature**: 1.0
- **Max Tokens**: None
- **Max Reasoning Tokens**: 0

### Dataset
- **Test Dataset**: ../../train.csv
- **Solution File**: ../../train_solution.csv

### Execution
- **Number of Runs**: 5
- **Start Time**: 2026-03-01 13:31:01
- **End Time**: 2026-03-01 13:31:51
- **Duration**: 0:00:49.313937

### Message
Training dataset. Baseline. Zeroshot. Forcing no reasoning.

## Results Summary

- **Mean Accuracy**: 0.5143 ± 0.0300
- **Total Cost**: $0.0075
- **Total Tokens**: 89,328
  - Prompt Tokens: 87,755
  - Completion Tokens: 1,573
- **Total API Requests**: 245

## Performance per Run

| Run | Accuracy | Correct / Total | Cost ($) | Tokens (Prompt + Completion) |
|-----|----------|---------------|----------|-----------------------------|
| 1 | 0.4898 | 24 / 49 | $0.0015 | 17,865 (17,551 + 314) |
| 2 | 0.5510 | 27 / 49 | $0.0017 | 17,863 (17,551 + 312) |
| 3 | 0.5306 | 26 / 49 | $0.0015 | 17,869 (17,551 + 318) |
| 4 | 0.5306 | 26 / 49 | $0.0016 | 17,865 (17,551 + 314) |
| 5 | 0.4694 | 23 / 49 | $0.0013 | 17,866 (17,551 + 315) |

## Cost Efficiency Analysis

### Overall Metrics

- **Cost per 1% Accuracy**: $0.014646
- **Tokens per 1% Accuracy**: 173693.3
- **Average Cost per Question**: $0.000154
- **Average Tokens per Question**: 1823.0

### Average Per Run

- **Average Cost per Run**: $0.001506
- **Average Tokens per Run**: 17865.6
  - Prompt Tokens: 17551.0
  - Completion Tokens: 314.6
