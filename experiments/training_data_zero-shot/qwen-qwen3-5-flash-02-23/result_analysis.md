# Solution Analysis Report
Generated: 2026-03-01 15:56:40

## Configuration

### Model Parameters
- **Model**: qwen/qwen3.5-flash-02-23
- **Temperature**: 1.0
- **Max Tokens**: None
- **Max Reasoning Tokens**: 600

### Dataset
- **Test Dataset**: ../../train.csv
- **Solution File**: ../../train_solution.csv

### Execution
- **Number of Runs**: 5
- **Start Time**: 2026-03-01 15:03:28
- **End Time**: 2026-03-01 15:56:40
- **Duration**: 0:53:11.789013

### Message
Training dataset. Baseline. Zeroshot. Allow reasonig for reasoning model.

## Results Summary

- **Mean Accuracy**: 0.7755 ± 0.0387
- **Total Cost**: $0.4221
- **Total Tokens**: 1,093,801
  - Prompt Tokens: 51,343
  - Completion Tokens: 1,042,458
- **Total API Requests**: 236

## Performance per Run

| Run | Accuracy | Correct / Total | Cost ($) | Tokens (Prompt + Completion) |
|-----|----------|---------------|----------|-----------------------------|
| 1 | 0.7347 | 36 / 49 | $0.0804 | 208,242 (9,578 + 198,664) |
| 2 | 0.7959 | 39 / 49 | $0.0853 | 221,190 (10,685 + 210,505) |
| 3 | 0.7347 | 36 / 49 | $0.0853 | 220,797 (9,936 + 210,861) |
| 4 | 0.8367 | 41 / 49 | $0.0805 | 209,032 (10,459 + 198,573) |
| 5 | 0.7755 | 38 / 49 | $0.0906 | 234,540 (10,685 + 223,855) |

## Cost Efficiency Analysis

### Overall Metrics

- **Cost per 1% Accuracy**: $0.544309
- **Tokens per 1% Accuracy**: 1410427.6
- **Average Cost per Question**: $0.008615
- **Average Tokens per Question**: 22322.5

### Average Per Run

- **Average Cost per Run**: $0.084424
- **Average Tokens per Run**: 218760.2
  - Prompt Tokens: 10268.6
  - Completion Tokens: 208491.6
