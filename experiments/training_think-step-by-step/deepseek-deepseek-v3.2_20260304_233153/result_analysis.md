# Solution Analysis Report
Generated: 2026-03-05 00:20:14

## Configuration

### Model Parameters
- **Model**: deepseek/deepseek-v3.2
- **Temperature**: 1.0
- **Max Tokens**: None
- **Max Reasoning Tokens**: 0

### Dataset
- **Test Dataset**: C:\Users\zzg_s\OneDrive - CentraleSupelec\Code\Python\scripts_gair_2026\experiments\train.csv
- **Solution File**: C:\Users\zzg_s\OneDrive - CentraleSupelec\Code\Python\scripts_gair_2026\experiments\train_solution.csv

### Execution
- **Number of Runs**: 5
- **Start Time**: 2026-03-04 23:31:53
- **End Time**: 2026-03-05 00:20:14
- **Duration**: 0:48:20.704222

### Message
Training dataset. We force the model not the reason, but 'think lound' using a chain-of-thoughts.

## Results Summary

- **Mean Accuracy**: 0.7918 ± 0.0153
- **Mean Kaggle Score**: 0.7876
- **Total Cost**: $0.1409
- **Total Tokens**: 315,421
  - Prompt Tokens: 51,455
  - Completion Tokens: 263,966
- **Total API Requests**: 245

## Performance per Run

| Run | Accuracy | Kaggle Score | Correct / Total | Cost ($) | Tokens (Prompt + Completion) |
|-----|----------|--------------|-----------------|----------|-----------------------------|
| 1 | 0.7959 | 0.7910 | 39 / 49 | $0.0330 | 59,130 (10,291 + 48,839) |
| 2 | 0.8163 | 0.8127 | 40 / 49 | $0.0242 | 63,787 (10,291 + 53,496) |
| 3 | 0.7959 | 0.7915 | 39 / 49 | $0.0298 | 70,034 (10,291 + 59,743) |
| 4 | 0.7755 | 0.7711 | 38 / 49 | $0.0296 | 63,306 (10,291 + 53,015) |
| 5 | 0.7755 | 0.7718 | 38 / 49 | $0.0245 | 59,164 (10,291 + 48,873) |

## Per-question results
| Question ID | Prediction_1 | Prediction_2 | Prediction_3 | Prediction_4 | Prediction_5 | Correct Answer | Accuracy |
|-------------|--------------|--------------|--------------|--------------|--------------|----------------|----------|
| 7 | d | d | d | d | d | a | 0.00 |
| 20 | a, b, c | a, c | a, b, c | a, c | a, b, c | a, b, c, d | 0.00 |
| 23 | c | c | a | a | c | b | 0.00 |
| 24 | a | a | nan | a | a | a, b, c | 0.00 |
| 28 | a | a | a | a | a | a, d | 0.00 |
| 39 | c | c | c | c | d | b | 0.00 |
| 45 | d | d | d | d | d | a | 0.00 |
| 25 | a | b | b | c | c | a | 0.20 |
| 26 | c | d | c | c | c | d | 0.20 |
| 35 | a | a | d | c | b | c | 0.20 |
| 13 | a, b, c | a, b, c | a, b, c | a, c | a, b, c | a, b, c | 0.80 |
| 29 | c | c | c | c | d | c | 0.80 |
| 40 | c | d | d | d | d | d | 0.80 |
| 46 | c | c | c | d | c | c | 0.80 |
| 1 | b | b | b | b | b | b | 1.00 |
| 2 | a, b | a, b | a, b | a, b | a, b | a, b | 1.00 |
| 3 | d | d | d | d | d | d | 1.00 |
| 4 | b | b | b | b | b | b | 1.00 |
| 5 | d | d | d | d | d | d | 1.00 |
| 6 | a | a | a | a | a | a | 1.00 |
| 8 | d | d | d | d | d | d | 1.00 |
| 9 | a, b | a, b | a, b | a, b | a, b | a, b | 1.00 |
| 10 | a | a | a | a | a | a | 1.00 |
| 11 | a | a | a | a | a | a | 1.00 |
| 12 | d | d | d | d | d | d | 1.00 |
| 14 | a, b, c, d | a, b, c, d | a, b, c, d | a, b, c, d | a, b, c, d | a, b, c, d | 1.00 |
| 15 | a | a | a | a | a | a | 1.00 |
| 16 | c | c | c | c | c | c | 1.00 |
| 17 | a | a | a | a | a | a | 1.00 |
| 18 | a | a | a | a | a | a | 1.00 |
| 19 | a, c | a, c | a, c | a, c | a, c | a, c | 1.00 |
| 21 | c | c | c | c | c | c | 1.00 |
| 22 | c | c | c | c | c | c | 1.00 |
| 27 | b | b | b | b | b | b | 1.00 |
| 30 | b | b | b | b | b | b | 1.00 |
| 31 | a | a | a | a | a | a | 1.00 |
| 32 | c | c | c | c | c | c | 1.00 |
| 33 | c | c | c | c | c | c | 1.00 |
| 34 | c | c | c | c | c | c | 1.00 |
| 36 | d | d | d | d | d | d | 1.00 |
| 37 | b | b | b | b | b | b | 1.00 |
| 38 | b | b | b | b | b | b | 1.00 |
| 41 | d | d | d | d | d | d | 1.00 |
| 42 | d | d | d | d | d | d | 1.00 |
| 43 | a | a | a | a | a | a | 1.00 |
| 44 | a | a | a | a | a | a | 1.00 |
| 47 | b | b | b | b | b | b | 1.00 |
| 48 | a | a | a | a | a | a | 1.00 |
| 49 | d | d | d | d | d | d | 1.00 |

## Cost Efficiency Analysis

### Overall Metrics

- **Average cost per 1% Accuracy (dollar cents)**: $0.035599
- **Average tokens per 1% Accuracy**: 796.7
- **Average Cost per Question**: $0.000575
- **Average Tokens per Question**: 1287.4

### Average Per Run

- **Average Cost per Run**: $0.028188
- **Average Tokens per Run**: 63084.2
  - Prompt Tokens: 10291.0
  - Completion Tokens: 52793.2
