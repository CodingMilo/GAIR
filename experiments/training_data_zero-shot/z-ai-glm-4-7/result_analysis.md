# Solution Analysis Report
Generated: 2026-03-01 20:29:19

## Configuration

### Model Parameters
- **Model**: z-ai/glm-4.7
- **Temperature**: 1.0
- **Max Tokens**: None
- **Max Reasoning Tokens**: 600

### Dataset
- **Test Dataset**: ../../train.csv
- **Solution File**: ../../train_solution.csv

### Execution
- **Number of Runs**: 5
- **Start Time**: 2026-03-01 17:07:10
- **End Time**: 2026-03-01 20:29:19
- **Duration**: 3:22:09.561249

### Message
Training dataset. Baseline. Zeroshot. Allow reasonig for reasoning model.

## Results Summary

- **Mean Accuracy**: 0.8163 ± 0.0289
- **Total Cost**: $2.4797
- **Total Tokens**: 1,329,950
  - Prompt Tokens: 49,294
  - Completion Tokens: 1,280,656
- **Total API Requests**: 245

## Performance per Run

| Run | Accuracy | Correct / Total | Cost ($) | Tokens (Prompt + Completion) |
|-----|----------|---------------|----------|-----------------------------|
| 1 | 0.8163 | 40 / 49 | $0.5089 | 288,127 (9,778 + 278,349) |
| 2 | 0.7755 | 38 / 49 | $0.5224 | 279,157 (9,851 + 269,306) |
| 3 | 0.8571 | 42 / 49 | $0.4536 | 270,026 (9,907 + 260,119) |
| 4 | 0.8367 | 41 / 49 | $0.4827 | 239,648 (9,851 + 229,797) |
| 5 | 0.7959 | 39 / 49 | $0.5121 | 252,992 (9,907 + 243,085) |

## Cost Efficiency Analysis

### Overall Metrics

- **Cost per 1% Accuracy**: $3.037652
- **Tokens per 1% Accuracy**: 1629188.8
- **Average Cost per Question**: $0.050606
- **Average Tokens per Question**: 27141.8

### Average Per Run

- **Average Cost per Run**: $0.495943
- **Average Tokens per Run**: 265990.0
  - Prompt Tokens: 9858.8
  - Completion Tokens: 256131.2
