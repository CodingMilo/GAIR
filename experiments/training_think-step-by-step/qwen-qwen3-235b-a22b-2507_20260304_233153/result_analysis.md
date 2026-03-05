# Solution Analysis Report
Generated: 2026-03-05 00:31:04

## Configuration

### Model Parameters
- **Model**: qwen/qwen3-235b-a22b-2507
- **Temperature**: 1.0
- **Max Tokens**: None
- **Max Reasoning Tokens**: 0

### Dataset
- **Test Dataset**: C:\Users\zzg_s\OneDrive - CentraleSupelec\Code\Python\scripts_gair_2026\experiments\train.csv
- **Solution File**: C:\Users\zzg_s\OneDrive - CentraleSupelec\Code\Python\scripts_gair_2026\experiments\train_solution.csv

### Execution
- **Number of Runs**: 5
- **Start Time**: 2026-03-04 23:44:15
- **End Time**: 2026-03-05 00:31:04
- **Duration**: 0:46:49.028160

### Message
Training dataset. We force the model not the reason, but 'think lound' using a chain-of-thoughts.

## Results Summary

- **Mean Accuracy**: 0.8204 ± 0.0327
- **Mean Kaggle Score**: 0.8134
- **Total Cost**: $0.2325
- **Total Tokens**: 521,273
  - Prompt Tokens: 55,318
  - Completion Tokens: 465,955
- **Total API Requests**: 245

## Performance per Run

| Run | Accuracy | Kaggle Score | Correct / Total | Cost ($) | Tokens (Prompt + Completion) |
|-----|----------|--------------|-----------------|----------|-----------------------------|
| 1 | 0.8367 | 0.8291 | 41 / 49 | $0.0511 | 112,618 (11,108 + 101,510) |
| 2 | 0.8367 | 0.8302 | 41 / 49 | $0.0437 | 84,894 (10,886 + 74,008) |
| 3 | 0.7551 | 0.7465 | 37 / 49 | $0.0571 | 110,224 (11,108 + 99,116) |
| 4 | 0.8367 | 0.8302 | 41 / 49 | $0.0434 | 105,887 (11,108 + 94,779) |
| 5 | 0.8367 | 0.8312 | 41 / 49 | $0.0372 | 107,650 (11,108 + 96,542) |

## Per-question results
| Question ID | Prediction_1 | Prediction_2 | Prediction_3 | Prediction_4 | Prediction_5 | Correct Answer | Accuracy |
|-------------|--------------|--------------|--------------|--------------|--------------|----------------|----------|
| 24 | a, b, c, d, c, a, b, c, d, c, a, b, c, d, c | a, b, c, d, a, b, c, d, c, c | c | a, b, c, d | c | a, b, c | 0.00 |
| 28 | a | a | nan | a | a | a, d | 0.00 |
| 39 | c | a, b, c, d | c | c | c | b | 0.00 |
| 45 | d | d | d | d | d | a | 0.00 |
| 46 | d | d | d | d | d | c | 0.00 |
| 23 | a | a | a | b | a | b | 0.20 |
| 35 | a | c | b | a | a | c | 0.20 |
| 20 | a, b, c, d | a, b, c | a, c, d | a, b, c | a, b, c, d | a, b, c, d | 0.40 |
| 25 | b | b | a | a | c | a | 0.40 |
| 7 | a | a | d | d | a | a | 0.60 |
| 11 | a | a | b | a | a | a | 0.80 |
| 16 | c | c | b | c | c | c | 0.80 |
| 19 | a, c | a, c | b, d | a, c | a, c | a, c | 0.80 |
| 1 | b | b | b | b | b | b | 1.00 |
| 2 | a, b | a, b | a, b | a, b | a, b | a, b | 1.00 |
| 3 | d | d | d | d | d | d | 1.00 |
| 4 | b | b | b | b | b | b | 1.00 |
| 5 | d | d | d | d | d | d | 1.00 |
| 6 | a | a | a | a | a | a | 1.00 |
| 8 | d | d | d | d | d | d | 1.00 |
| 9 | a, b | a, b | a, b | a, b | a, b | a, b | 1.00 |
| 10 | a | a | a | a | a | a | 1.00 |
| 12 | d | d | d | d | d | d | 1.00 |
| 13 | a, b, c | a, b, c | a, b, c | a, b, c | a, b, c | a, b, c | 1.00 |
| 14 | a, b, c, d | a, b, c, d | a, b, c, d | a, b, c, d | a, b, c, d | a, b, c, d | 1.00 |
| 15 | a | a | a | a | a | a | 1.00 |
| 17 | a | a | a | a | a | a | 1.00 |
| 18 | a | a | a | a | a | a | 1.00 |
| 21 | c | c | c | c | c | c | 1.00 |
| 22 | c | c | c | c | c | c | 1.00 |
| 26 | d | d | d | d | d | d | 1.00 |
| 27 | b | b | b | b | b | b | 1.00 |
| 29 | c | c | c | c | c | c | 1.00 |
| 30 | b | b | b | b | b | b | 1.00 |
| 31 | a | a | a | a | a | a | 1.00 |
| 32 | c | c | c | c | c | c | 1.00 |
| 33 | c | c | c | c | c | c | 1.00 |
| 34 | c | c | c | c | c | c | 1.00 |
| 36 | d | d | d | d | d | d | 1.00 |
| 37 | b | b | b | b | b | b | 1.00 |
| 38 | b | b | b | b | b | b | 1.00 |
| 40 | d | d | d | d | d | d | 1.00 |
| 41 | d | d | d | d | d | d | 1.00 |
| 42 | d | d | d | d | d | d | 1.00 |
| 43 | a | a | a | a | a | a | 1.00 |
| 44 | a | a | a | a | a | a | 1.00 |
| 47 | b | b | b | b | b | b | 1.00 |
| 48 | a | a | a | a | a | a | 1.00 |
| 49 | d | d | d | d | d | d | 1.00 |

## Cost Efficiency Analysis

### Overall Metrics

- **Average cost per 1% Accuracy (dollar cents)**: $0.056682
- **Average tokens per 1% Accuracy**: 1270.8
- **Average Cost per Question**: $0.000949
- **Average Tokens per Question**: 2127.6

### Average Per Run

- **Average Cost per Run**: $0.046502
- **Average Tokens per Run**: 104254.6
  - Prompt Tokens: 11063.6
  - Completion Tokens: 93191.0
