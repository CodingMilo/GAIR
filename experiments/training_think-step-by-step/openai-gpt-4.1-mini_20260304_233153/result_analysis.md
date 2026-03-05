# Solution Analysis Report
Generated: 2026-03-05 00:31:01

## Configuration

### Model Parameters
- **Model**: openai/gpt-4.1-mini
- **Temperature**: 1.0
- **Max Tokens**: None
- **Max Reasoning Tokens**: 0

### Dataset
- **Test Dataset**: C:\Users\zzg_s\OneDrive - CentraleSupelec\Code\Python\scripts_gair_2026\experiments\train.csv
- **Solution File**: C:\Users\zzg_s\OneDrive - CentraleSupelec\Code\Python\scripts_gair_2026\experiments\train_solution.csv

### Execution
- **Number of Runs**: 5
- **Start Time**: 2026-03-05 00:20:14
- **End Time**: 2026-03-05 00:31:01
- **Duration**: 0:10:47.457062

### Message
Training dataset. We force the model not the reason, but 'think lound' using a chain-of-thoughts.

## Results Summary

- **Mean Accuracy**: 0.6980 ± 0.0327
- **Mean Kaggle Score**: 0.6872
- **Total Cost**: $0.3579
- **Total Tokens**: 263,464
  - Prompt Tokens: 53,015
  - Completion Tokens: 210,449
- **Total API Requests**: 245

## Performance per Run

| Run | Accuracy | Kaggle Score | Correct / Total | Cost ($) | Tokens (Prompt + Completion) |
|-----|----------|--------------|-----------------|----------|-----------------------------|
| 1 | 0.6531 | 0.6419 | 32 / 49 | $0.0744 | 54,436 (10,603 + 43,833) |
| 2 | 0.6939 | 0.6825 | 34 / 49 | $0.0757 | 55,293 (10,603 + 44,690) |
| 3 | 0.7347 | 0.7244 | 36 / 49 | $0.0687 | 50,891 (10,603 + 40,288) |
| 4 | 0.7347 | 0.7247 | 36 / 49 | $0.0667 | 49,659 (10,603 + 39,056) |
| 5 | 0.6735 | 0.6626 | 33 / 49 | $0.0724 | 53,185 (10,603 + 42,582) |

## Per-question results
| Question ID | Prediction_1 | Prediction_2 | Prediction_3 | Prediction_4 | Prediction_5 | Correct Answer | Accuracy |
|-------------|--------------|--------------|--------------|--------------|--------------|----------------|----------|
| 7 | c | d | d | c | d | a | 0.00 |
| 19 | b, d | b, d | b, d | b, c | b, d | a, c | 0.00 |
| 23 | a | d | c | a | c | b | 0.00 |
| 24 | b | a, b, c, d | a, b, c, d | a | a | a, b, c | 0.00 |
| 26 | c | b | b | b | b | d | 0.00 |
| 28 | a | a | a | a | a | a, d | 0.00 |
| 35 | a | d | a | a | a | c | 0.00 |
| 39 | c | d | c | c | d | b | 0.00 |
| 45 | d | d | d | d | d | a | 0.00 |
| 13 | a, c | a, c | a, b, c | a, c | a, c | a, b, c | 0.20 |
| 14 | a, b, c | a, b, c | a, b, c, d | a, b, c | a, b, c | a, b, c, d | 0.20 |
| 20 | a, b, c | a, b, c | a, b, c | a, b, c, d | a, b, c | a, b, c, d | 0.20 |
| 46 | c | b | b | b | a | c | 0.20 |
| 29 | d | d | c | d | c | c | 0.40 |
| 11 | a | b | a | a | b | a | 0.60 |
| 30 | a | b | a | b | b | b | 0.60 |
| 33 | a | c | c | c | a | c | 0.60 |
| 40 | c | d | a, b, c, d | d | d | d | 0.60 |
| 10 | d | a | a | a | a | a | 0.80 |
| 17 | a | a | a | a | d | a | 0.80 |
| 1 | b | b | b | b | b | b | 1.00 |
| 2 | a, b | a, b | a, b | a, b | a, b | a, b | 1.00 |
| 3 | d | d | d | d | d | d | 1.00 |
| 4 | b | b | b | b | b | b | 1.00 |
| 5 | d | d | d | d | d | d | 1.00 |
| 6 | a | a | a | a | a | a | 1.00 |
| 8 | d | d | d | d | d | d | 1.00 |
| 9 | a, b | a, b | a, b | a, b | a, b | a, b | 1.00 |
| 12 | d | d | d | d | d | d | 1.00 |
| 15 | a | a | a | a | a | a | 1.00 |
| 16 | c | c | c | c | c | c | 1.00 |
| 18 | a | a | a | a | a | a | 1.00 |
| 21 | c | c | c | c | c | c | 1.00 |
| 22 | c | c | c | c | c | c | 1.00 |
| 25 | a | a | a | a | a | a | 1.00 |
| 27 | b | b | b | b | b | b | 1.00 |
| 31 | a | a | a | a | a | a | 1.00 |
| 32 | c | c | c | c | c | c | 1.00 |
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

- **Average cost per 1% Accuracy (dollar cents)**: $0.102563
- **Average tokens per 1% Accuracy**: 755.0
- **Average Cost per Question**: $0.001461
- **Average Tokens per Question**: 1075.4

### Average Per Run

- **Average Cost per Run**: $0.071585
- **Average Tokens per Run**: 52692.8
  - Prompt Tokens: 10603.0
  - Completion Tokens: 42089.8
