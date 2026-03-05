# Solution Analysis Report
Generated: 2026-03-01 15:01:53

## Configuration

### Model Parameters
- **Model**: x-ai/grok-4.1-fast
- **Temperature**: 1.0
- **Max Tokens**: None
- **Max Reasoning Tokens**: 600

### Dataset
- **Test Dataset**: ../../train.csv
- **Solution File**: ../../train_solution.csv

### Execution
- **Number of Runs**: 5
- **Start Time**: 2026-03-01 14:10:48
- **End Time**: 2026-03-01 15:01:53
- **Duration**: 0:51:04.526603

### Message
Training dataset. Baseline. Zeroshot. Allow reasonig for reasoning model.

## Results Summary

- **Mean Accuracy**: 0.8122 ± 0.0153
- **Total Cost**: $0.4055
- **Total Tokens**: 878,206
  - Prompt Tokens: 83,835
  - Completion Tokens: 794,371
- **Total API Requests**: 245

## Performance per Run

| Run | Accuracy | Correct / Total | Cost ($) | Tokens (Prompt + Completion) |
|-----|----------|---------------|----------|-----------------------------|
| 1 | 0.8367 | 41 / 49 | $0.0776 | 168,614 (16,767 + 151,847) |
| 2 | 0.8163 | 40 / 49 | $0.0808 | 175,268 (16,767 + 158,501) |
| 3 | 0.7959 | 39 / 49 | $0.0836 | 181,548 (16,767 + 164,781) |
| 4 | 0.7959 | 39 / 49 | $0.0743 | 161,008 (16,767 + 144,241) |
| 5 | 0.8163 | 40 / 49 | $0.0893 | 191,768 (16,767 + 175,001) |

## Cost Efficiency Analysis

### Overall Metrics

- **Cost per 1% Accuracy**: $0.499204
- **Tokens per 1% Accuracy**: 1081208.4
- **Average Cost per Question**: $0.008275
- **Average Tokens per Question**: 17922.6

### Average Per Run

- **Average Cost per Run**: $0.081095
- **Average Tokens per Run**: 175641.2
  - Prompt Tokens: 16767.0
  - Completion Tokens: 158874.2
