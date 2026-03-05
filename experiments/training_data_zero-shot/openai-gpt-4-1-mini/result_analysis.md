# Solution Analysis Report
Generated: 2026-03-01 13:57:09

## Configuration

### Model Parameters
- **Model**: openai/gpt-4.1-mini
- **Temperature**: 1.0
- **Max Tokens**: None
- **Max Reasoning Tokens**: 600

### Dataset
- **Test Dataset**: ../../train.csv
- **Solution File**: ../../train_solution.csv

### Execution
- **Number of Runs**: 5
- **Start Time**: 2026-03-01 13:55:16
- **End Time**: 2026-03-01 13:57:09
- **Duration**: 0:01:52.701562

### Message
Training dataset. Baseline. Zeroshot. Allow reasonig for reasoning model.

## Results Summary

- **Mean Accuracy**: 0.4694 ± 0.0289
- **Total Cost**: $0.0311
- **Total Tokens**: 57,181
  - Prompt Tokens: 50,320
  - Completion Tokens: 6,861
- **Total API Requests**: 245

## Performance per Run

| Run | Accuracy | Correct / Total | Cost ($) | Tokens (Prompt + Completion) |
|-----|----------|---------------|----------|-----------------------------|
| 1 | 0.4490 | 22 / 49 | $0.0047 | 10,482 (10,064 + 418) |
| 2 | 0.4898 | 24 / 49 | $0.0123 | 15,234 (10,064 + 5,170) |
| 3 | 0.4286 | 21 / 49 | $0.0047 | 10,489 (10,064 + 425) |
| 4 | 0.5102 | 25 / 49 | $0.0047 | 10,488 (10,064 + 424) |
| 5 | 0.4694 | 23 / 49 | $0.0047 | 10,488 (10,064 + 424) |

## Cost Efficiency Analysis

### Overall Metrics

- **Cost per 1% Accuracy**: $0.066268
- **Tokens per 1% Accuracy**: 121820.4
- **Average Cost per Question**: $0.000635
- **Average Tokens per Question**: 1167.0

### Average Per Run

- **Average Cost per Run**: $0.006221
- **Average Tokens per Run**: 11436.2
  - Prompt Tokens: 10064.0
  - Completion Tokens: 1372.2
