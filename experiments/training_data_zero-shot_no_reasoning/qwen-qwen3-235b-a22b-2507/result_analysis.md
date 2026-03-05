# Solution Analysis Report
Generated: 2026-03-01 13:26:56

## Configuration

### Model Parameters
- **Model**: qwen/qwen3-235b-a22b-2507
- **Temperature**: 1.0
- **Max Tokens**: None
- **Max Reasoning Tokens**: 0

### Dataset
- **Test Dataset**: ../../train.csv
- **Solution File**: ../../train_solution.csv

### Execution
- **Number of Runs**: 5
- **Start Time**: 2026-03-01 13:10:49
- **End Time**: 2026-03-01 13:26:56
- **Duration**: 0:16:06.670007

### Message
Training dataset. Baseline. Zeroshot. Forcing no reasoning.

## Results Summary

- **Mean Accuracy**: 0.5959 ± 0.0271
- **Total Cost**: $0.0078
- **Total Tokens**: 66,420
  - Prompt Tokens: 53,937
  - Completion Tokens: 12,483
- **Total API Requests**: 245

## Performance per Run

| Run | Accuracy | Correct / Total | Cost ($) | Tokens (Prompt + Completion) |
|-----|----------|---------------|----------|-----------------------------|
| 1 | 0.6122 | 30 / 49 | $0.0015 | 11,314 (10,789 + 525) |
| 2 | 0.5918 | 29 / 49 | $0.0017 | 15,798 (10,797 + 5,001) |
| 3 | 0.6327 | 31 / 49 | $0.0014 | 12,160 (10,789 + 1,371) |
| 4 | 0.5918 | 29 / 49 | $0.0015 | 13,197 (10,789 + 2,408) |
| 5 | 0.5510 | 27 / 49 | $0.0017 | 13,951 (10,773 + 3,178) |

## Cost Efficiency Analysis

### Overall Metrics

- **Cost per 1% Accuracy**: $0.013056
- **Tokens per 1% Accuracy**: 111458.2
- **Average Cost per Question**: $0.000159
- **Average Tokens per Question**: 1355.5

### Average Per Run

- **Average Cost per Run**: $0.001556
- **Average Tokens per Run**: 13284.0
  - Prompt Tokens: 10787.4
  - Completion Tokens: 2496.6
