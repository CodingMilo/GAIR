# Solution Analysis Report
Generated: 2026-03-01 18:17:15

## Configuration

### Model Parameters
- **Model**: deepseek/deepseek-v3.2
- **Temperature**: 1.0
- **Max Tokens**: None
- **Max Reasoning Tokens**: 600

### Dataset
- **Test Dataset**: ../../train.csv
- **Solution File**: ../../train_solution.csv

### Execution
- **Number of Runs**: 5
- **Start Time**: 2026-03-01 14:03:27
- **End Time**: 2026-03-01 18:17:15
- **Duration**: 4:13:47.800289

### Message
Training dataset. Baseline. Zeroshot. Allow reasonig for reasoning model.

## Results Summary

- **Mean Accuracy**: 0.8327 ± 0.0238
- **Total Cost**: $0.5239
- **Total Tokens**: 1,102,705
  - Prompt Tokens: 49,692
  - Completion Tokens: 1,053,013
- **Total API Requests**: 245

## Performance per Run

| Run | Accuracy | Correct / Total | Cost ($) | Tokens (Prompt + Completion) |
|-----|----------|---------------|----------|-----------------------------|
| 1 | 0.8367 | 41 / 49 | $0.0970 | 220,257 (9,948 + 210,309) |
| 2 | 0.8776 | 43 / 49 | $0.0891 | 217,576 (9,948 + 207,628) |
| 3 | 0.8163 | 40 / 49 | $0.1048 | 218,481 (9,906 + 208,575) |
| 4 | 0.8163 | 40 / 49 | $0.0977 | 221,706 (9,948 + 211,758) |
| 5 | 0.8163 | 40 / 49 | $0.1353 | 224,685 (9,942 + 214,743) |

## Cost Efficiency Analysis

### Overall Metrics

- **Cost per 1% Accuracy**: $0.629173
- **Tokens per 1% Accuracy**: 1324327.1
- **Average Cost per Question**: $0.010691
- **Average Tokens per Question**: 22504.2

### Average Per Run

- **Average Cost per Run**: $0.104777
- **Average Tokens per Run**: 220541.0
  - Prompt Tokens: 9938.4
  - Completion Tokens: 210602.6
