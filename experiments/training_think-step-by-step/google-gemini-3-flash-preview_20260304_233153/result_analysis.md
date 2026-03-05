# Solution Analysis Report
Generated: 2026-03-05 00:40:35

## Configuration

### Model Parameters
- **Model**: google/gemini-3-flash-preview
- **Temperature**: 1.0
- **Max Tokens**: None
- **Max Reasoning Tokens**: 0

### Dataset
- **Test Dataset**: C:\Users\zzg_s\OneDrive - CentraleSupelec\Code\Python\scripts_gair_2026\experiments\train.csv
- **Solution File**: C:\Users\zzg_s\OneDrive - CentraleSupelec\Code\Python\scripts_gair_2026\experiments\train_solution.csv

### Execution
- **Number of Runs**: 5
- **Start Time**: 2026-03-05 00:31:04
- **End Time**: 2026-03-05 00:40:35
- **Duration**: 0:09:30.785755

### Message
Training dataset. We force the model not the reason, but 'think lound' using a chain-of-thoughts.

## Results Summary

- **Mean Accuracy**: 0.8449 ± 0.0100
- **Mean Kaggle Score**: 0.8314
- **Total Cost**: $0.4506
- **Total Tokens**: 195,406
  - Prompt Tokens: 54,262
  - Completion Tokens: 141,144
- **Total API Requests**: 245

## Performance per Run

| Run | Accuracy | Kaggle Score | Correct / Total | Cost ($) | Tokens (Prompt + Completion) |
|-----|----------|--------------|-----------------|----------|-----------------------------|
| 1 | 0.8367 | 0.8231 | 41 / 49 | $0.0907 | 39,268 (10,856 + 28,412) |
| 2 | 0.8367 | 0.8233 | 41 / 49 | $0.0896 | 38,916 (10,840 + 28,076) |
| 3 | 0.8571 | 0.8438 | 42 / 49 | $0.0889 | 38,686 (10,858 + 27,828) |
| 4 | 0.8571 | 0.8437 | 42 / 49 | $0.0894 | 38,830 (10,852 + 27,978) |
| 5 | 0.8367 | 0.8229 | 41 / 49 | $0.0920 | 39,706 (10,856 + 28,850) |

## Per-question results
| Question ID | Prediction_1 | Prediction_2 | Prediction_3 | Prediction_4 | Prediction_5 | Correct Answer | Accuracy |
|-------------|--------------|--------------|--------------|--------------|--------------|----------------|----------|
| 23 | c | c | c | c | c | b | 0.00 |
| 24 | a, b, c, d, a, b, c, d, b, c, d | a | a | a, b, c, d, c | a | a, b, c | 0.00 |
| 28 | a | a | a | a | a | a, d | 0.00 |
| 35 | d | a | a | a | a | c | 0.00 |
| 39 | d | a | d | d | a | b | 0.00 |
| 45 | d | d | d | d | d | a | 0.00 |
| 25 | b | b | a | b | b | a | 0.20 |
| 13 | a, b, c | b, c | b | a, b, c | a, b, c | a, b, c | 0.60 |
| 14 | a, b, c, d | a, b, c, d | a, b, c, d | a, b, c, d | a, b, c | a, b, c, d | 0.80 |
| 20 | a, c, d | a, b, c, d | a, b, c, d | a, b, c, d | a, b, c, d | a, b, c, d | 0.80 |
| 1 | b | b | b | b | b | b | 1.00 |
| 2 | a, b | a, b | a, b | a, b | a, b | a, b | 1.00 |
| 3 | d | d | d | d | d | d | 1.00 |
| 4 | b | b | b | b | b | b | 1.00 |
| 5 | d | d | d | d | d | d | 1.00 |
| 6 | a | a | a | a | a | a | 1.00 |
| 7 | a | a | a | a | a | a | 1.00 |
| 8 | d | d | d | d | d | d | 1.00 |
| 9 | a, b | a, b | a, b | a, b | a, b | a, b | 1.00 |
| 10 | a | a | a | a | a | a | 1.00 |
| 11 | a | a | a | a | a | a | 1.00 |
| 12 | d | d | d | d | d | d | 1.00 |
| 15 | a | a | a | a | a | a | 1.00 |
| 16 | c | c | c | c | c | c | 1.00 |
| 17 | a | a | a | a | a | a | 1.00 |
| 18 | a | a | a | a | a | a | 1.00 |
| 19 | a, c | a, c | a, c | a, c | a, c | a, c | 1.00 |
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
| 46 | c | c | c | c | c | c | 1.00 |
| 47 | b | b | b | b | b | b | 1.00 |
| 48 | a | a | a | a | a | a | 1.00 |
| 49 | d | d | d | d | d | d | 1.00 |

## Cost Efficiency Analysis

### Overall Metrics

- **Average cost per 1% Accuracy (dollar cents)**: $0.106655
- **Average tokens per 1% Accuracy**: 462.6
- **Average Cost per Question**: $0.001839
- **Average Tokens per Question**: 797.6

### Average Per Run

- **Average Cost per Run**: $0.090113
- **Average Tokens per Run**: 39081.2
  - Prompt Tokens: 10852.4
  - Completion Tokens: 28228.8
