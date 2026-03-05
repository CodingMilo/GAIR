# Solution Analysis Report
Generated: 2026-03-01 17:04:54

## Configuration

### Model Parameters
- **Model**: qwen/qwen3.5-plus-02-15
- **Temperature**: 1.0
- **Max Tokens**: None
- **Max Reasoning Tokens**: 600

### Dataset
- **Test Dataset**: ../../train.csv
- **Solution File**: ../../train_solution.csv

### Execution
- **Number of Runs**: 5
- **Start Time**: 2026-03-01 15:56:40
- **End Time**: 2026-03-01 17:04:54
- **Duration**: 1:08:13.797502

### Message
Training dataset. Baseline. Zeroshot. Allow reasonig for reasoning model.

## Results Summary

- **Mean Accuracy**: 0.8327 ± 0.0153
- **Total Cost**: $1.9760
- **Total Tokens**: 867,871
  - Prompt Tokens: 53,425
  - Completion Tokens: 814,446
- **Total API Requests**: 245

## Performance per Run

| Run | Accuracy | Correct / Total | Cost ($) | Tokens (Prompt + Completion) |
|-----|----------|---------------|----------|-----------------------------|
| 1 | 0.8163 | 40 / 49 | $0.3784 | 166,569 (10,685 + 155,884) |
| 2 | 0.8571 | 42 / 49 | $0.4030 | 176,837 (10,685 + 166,152) |
| 3 | 0.8367 | 41 / 49 | $0.3852 | 169,410 (10,685 + 158,725) |
| 4 | 0.8163 | 40 / 49 | $0.3932 | 172,728 (10,685 + 162,043) |
| 5 | 0.8367 | 41 / 49 | $0.4162 | 182,327 (10,685 + 171,642) |

## Cost Efficiency Analysis

### Overall Metrics

- **Cost per 1% Accuracy**: $2.373186
- **Tokens per 1% Accuracy**: 1042296.1
- **Average Cost per Question**: $0.040327
- **Average Tokens per Question**: 17711.7

### Average Per Run

- **Average Cost per Run**: $0.395208
- **Average Tokens per Run**: 173574.2
  - Prompt Tokens: 10685.0
  - Completion Tokens: 162889.2
