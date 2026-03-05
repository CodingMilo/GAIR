# Solution Analysis Report
Generated: 2026-03-01 14:10:48

## Configuration

### Model Parameters
- **Model**: openai/gpt-5-mini
- **Temperature**: 1.0
- **Max Tokens**: None
- **Max Reasoning Tokens**: 600

### Dataset
- **Test Dataset**: ../../train.csv
- **Solution File**: ../../train_solution.csv

### Execution
- **Number of Runs**: 5
- **Start Time**: 2026-03-01 13:55:16
- **End Time**: 2026-03-01 14:10:48
- **Duration**: 0:15:32.107139

### Message
Training dataset. Baseline. Zeroshot. Allow reasonig for reasoning model.

## Results Summary

- **Mean Accuracy**: 0.7469 ± 0.0245
- **Total Cost**: $0.2426
- **Total Tokens**: 165,092
  - Prompt Tokens: 50,075
  - Completion Tokens: 115,017
- **Total API Requests**: 245

## Performance per Run

| Run | Accuracy | Correct / Total | Cost ($) | Tokens (Prompt + Completion) |
|-----|----------|---------------|----------|-----------------------------|
| 1 | 0.7755 | 38 / 49 | $0.0519 | 34,726 (10,015 + 24,711) |
| 2 | 0.7347 | 36 / 49 | $0.0453 | 31,431 (10,015 + 21,416) |
| 3 | 0.7143 | 35 / 49 | $0.0473 | 32,412 (10,015 + 22,397) |
| 4 | 0.7755 | 38 / 49 | $0.0503 | 33,897 (10,015 + 23,882) |
| 5 | 0.7347 | 36 / 49 | $0.0477 | 32,626 (10,015 + 22,611) |

## Cost Efficiency Analysis

### Overall Metrics

- **Cost per 1% Accuracy**: $0.324729
- **Tokens per 1% Accuracy**: 221024.8
- **Average Cost per Question**: $0.004950
- **Average Tokens per Question**: 3369.2

### Average Per Run

- **Average Cost per Run**: $0.048511
- **Average Tokens per Run**: 33018.4
  - Prompt Tokens: 10015.0
  - Completion Tokens: 23003.4
