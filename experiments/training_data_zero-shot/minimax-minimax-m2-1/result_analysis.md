# Solution Analysis Report
Generated: 2026-03-01 20:36:56

## Configuration

### Model Parameters
- **Model**: minimax/minimax-m2.1
- **Temperature**: 1.0
- **Max Tokens**: None
- **Max Reasoning Tokens**: 600

### Dataset
- **Test Dataset**: ../../train.csv
- **Solution File**: ../../train_solution.csv

### Execution
- **Number of Runs**: 5
- **Start Time**: 2026-03-01 18:17:15
- **End Time**: 2026-03-01 20:36:56
- **Duration**: 2:19:40.693674

### Message
Training dataset. Baseline. Zeroshot. Allow reasonig for reasoning model.

## Results Summary

- **Mean Accuracy**: 0.7837 ± 0.0277
- **Total Cost**: $1.4920
- **Total Tokens**: 1,261,649
  - Prompt Tokens: 52,203
  - Completion Tokens: 1,209,446
- **Total API Requests**: 245

## Performance per Run

| Run | Accuracy | Correct / Total | Cost ($) | Tokens (Prompt + Completion) |
|-----|----------|---------------|----------|-----------------------------|
| 1 | 0.8163 | 40 / 49 | $0.2487 | 236,181 (10,442 + 225,739) |
| 2 | 0.7959 | 39 / 49 | $0.2977 | 269,727 (10,436 + 259,291) |
| 3 | 0.7755 | 38 / 49 | $0.2459 | 220,515 (10,449 + 210,066) |
| 4 | 0.7347 | 36 / 49 | $0.4196 | 287,077 (10,430 + 276,647) |
| 5 | 0.7959 | 39 / 49 | $0.2801 | 248,149 (10,446 + 237,703) |

## Cost Efficiency Analysis

### Overall Metrics

- **Cost per 1% Accuracy**: $1.903853
- **Tokens per 1% Accuracy**: 1609916.7
- **Average Cost per Question**: $0.030449
- **Average Tokens per Question**: 25747.9

### Average Per Run

- **Average Cost per Run**: $0.298400
- **Average Tokens per Run**: 252329.8
  - Prompt Tokens: 10440.6
  - Completion Tokens: 241889.2
