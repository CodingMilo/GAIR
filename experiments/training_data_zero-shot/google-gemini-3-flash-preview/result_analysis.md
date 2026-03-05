# Solution Analysis Report
Generated: 2026-03-01 14:03:27

## Configuration

### Model Parameters
- **Model**: google/gemini-3-flash-preview
- **Temperature**: 1.0
- **Max Tokens**: None
- **Max Reasoning Tokens**: 600

### Dataset
- **Test Dataset**: ../../train.csv
- **Solution File**: ../../train_solution.csv

### Execution
- **Number of Runs**: 5
- **Start Time**: 2026-03-01 13:57:09
- **End Time**: 2026-03-01 14:03:27
- **Duration**: 0:06:18.218093

### Message
Training dataset. Baseline. Zeroshot. Allow reasonig for reasoning model.

## Results Summary

- **Mean Accuracy**: 0.7388 ± 0.0238
- **Total Cost**: $0.4408
- **Total Tokens**: 188,663
  - Prompt Tokens: 50,087
  - Completion Tokens: 138,576
- **Total API Requests**: 245

## Performance per Run

| Run | Accuracy | Correct / Total | Cost ($) | Tokens (Prompt + Completion) |
|-----|----------|---------------|----------|-----------------------------|
| 1 | 0.7347 | 36 / 49 | $0.0695 | 31,535 (10,023 + 21,512) |
| 2 | 0.7143 | 35 / 49 | $0.1625 | 62,499 (10,017 + 52,482) |
| 3 | 0.7143 | 35 / 49 | $0.0784 | 34,466 (10,017 + 24,449) |
| 4 | 0.7755 | 38 / 49 | $0.0696 | 31,547 (10,017 + 21,530) |
| 5 | 0.7551 | 37 / 49 | $0.0608 | 28,616 (10,013 + 18,603) |

## Cost Efficiency Analysis

### Overall Metrics

- **Cost per 1% Accuracy**: $0.596624
- **Tokens per 1% Accuracy**: 255372.6
- **Average Cost per Question**: $0.008995
- **Average Tokens per Question**: 3850.3

### Average Per Run

- **Average Cost per Run**: $0.088154
- **Average Tokens per Run**: 37732.6
  - Prompt Tokens: 10017.4
  - Completion Tokens: 27715.2
