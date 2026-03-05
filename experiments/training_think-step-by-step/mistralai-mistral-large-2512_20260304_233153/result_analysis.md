# Solution Analysis Report
Generated: 2026-03-04 23:44:14

## Configuration

### Model Parameters
- **Model**: mistralai/mistral-large-2512
- **Temperature**: 1.0
- **Max Tokens**: None
- **Max Reasoning Tokens**: 0

### Dataset
- **Test Dataset**: C:\Users\zzg_s\OneDrive - CentraleSupelec\Code\Python\scripts_gair_2026\experiments\train.csv
- **Solution File**: C:\Users\zzg_s\OneDrive - CentraleSupelec\Code\Python\scripts_gair_2026\experiments\train_solution.csv

### Execution
- **Number of Runs**: 5
- **Start Time**: 2026-03-04 23:31:53
- **End Time**: 2026-03-04 23:44:14
- **Duration**: 0:12:21.524818

### Message
Training dataset. We force the model not the reason, but 'think lound' using a chain-of-thoughts.

## Results Summary

- **Mean Accuracy**: 0.7429 ± 0.0208
- **Mean Kaggle Score**: 0.7332
- **Total Cost**: $0.3214
- **Total Tokens**: 250,626
  - Prompt Tokens: 54,510
  - Completion Tokens: 196,116
- **Total API Requests**: 245

## Performance per Run

| Run | Accuracy | Kaggle Score | Correct / Total | Cost ($) | Tokens (Prompt + Completion) |
|-----|----------|--------------|-----------------|----------|-----------------------------|
| 1 | 0.7347 | 0.7256 | 36 / 49 | $0.0609 | 47,900 (10,902 + 36,998) |
| 2 | 0.7143 | 0.7041 | 35 / 49 | $0.0679 | 52,544 (10,902 + 41,642) |
| 3 | 0.7755 | 0.7667 | 38 / 49 | $0.0584 | 46,223 (10,902 + 35,321) |
| 4 | 0.7551 | 0.7448 | 37 / 49 | $0.0689 | 53,209 (10,902 + 42,307) |
| 5 | 0.7347 | 0.7249 | 36 / 49 | $0.0652 | 50,750 (10,902 + 39,848) |

## Per-question results
| Question ID | Prediction_1 | Prediction_2 | Prediction_3 | Prediction_4 | Prediction_5 | Correct Answer | Accuracy |
|-------------|--------------|--------------|--------------|--------------|--------------|----------------|----------|
| 23 | a | a | a | a | a | b | 0.00 |
| 24 | b | a | c | c | a | a, b, c | 0.00 |
| 25 | b | c | b | b | b | a | 0.00 |
| 28 | a | a | a | a | a | a, d | 0.00 |
| 33 | d | d | b | d | b | c | 0.00 |
| 35 | a | b | a | b | b | c | 0.00 |
| 39 | c | c | c | c | c | b | 0.00 |
| 45 | d | d | d | d | d | a | 0.00 |
| 20 | a, b, c | a, b, c | a, b, c, d | a, c, d | a, b, c | a, b, c, d | 0.20 |
| 26 | c | c | d | c | c | d | 0.20 |
| 7 | b | d | a | d | a | a | 0.40 |
| 16 | b | b | c | c | c | c | 0.60 |
| 17 | a | a | b | a | b | a | 0.60 |
| 19 | b, d | a, c | a, c | b, d | a, c | a, c | 0.60 |
| 46 | c | c | a | c | d | c | 0.60 |
| 3 | d | d | c | d | d | d | 0.80 |
| 11 | a | b | a | a | a | a | 0.80 |
| 14 | a, b, c, d | a, b, c, d | a, b, c, d | a, b, c, d | a, b, c | a, b, c, d | 0.80 |
| 47 | b | a | b | b | b | b | 0.80 |
| 1 | b | b | b | b | b | b | 1.00 |
| 2 | a, b | a, b | a, b | a, b | a, b | a, b | 1.00 |
| 4 | b | b | b | b | b | b | 1.00 |
| 5 | d | d | d | d | d | d | 1.00 |
| 6 | a | a | a | a | a | a | 1.00 |
| 8 | d | d | d | d | d | d | 1.00 |
| 9 | a, b | a, b | a, b | a, b | a, b | a, b | 1.00 |
| 10 | a | a | a | a | a | a | 1.00 |
| 12 | d | d | d | d | d | d | 1.00 |
| 13 | a, b, c | a, b, c | a, b, c | a, b, c | a, b, c | a, b, c | 1.00 |
| 15 | a | a | a | a | a | a | 1.00 |
| 18 | a | a | a | a | a | a | 1.00 |
| 21 | c | c | c | c | c | c | 1.00 |
| 22 | c | c | c | c | c | c | 1.00 |
| 27 | b | b | b | b | b | b | 1.00 |
| 29 | c | c | c | c | c | c | 1.00 |
| 30 | b | b | b | b | b | b | 1.00 |
| 31 | a | a | a | a | a | a | 1.00 |
| 32 | c | c | c | c | c | c | 1.00 |
| 34 | c | c | c | c | c | c | 1.00 |
| 36 | d | d | d | d | d | d | 1.00 |
| 37 | b | b | b | b | b | b | 1.00 |
| 38 | b | b | b | b | b | b | 1.00 |
| 40 | d | d | d | d | d | d | 1.00 |
| 41 | d | d | d | d | d | d | 1.00 |
| 42 | d | d | d | d | d | d | 1.00 |
| 43 | a | a | a | a | a | a | 1.00 |
| 44 | a | a | a | a | a | a | 1.00 |
| 48 | a | a | a | a | a | a | 1.00 |
| 49 | d | d | d | d | d | d | 1.00 |

## Cost Efficiency Analysis

### Overall Metrics

- **Average cost per 1% Accuracy (dollar cents)**: $0.086539
- **Average tokens per 1% Accuracy**: 674.8
- **Average Cost per Question**: $0.001312
- **Average Tokens per Question**: 1023.0

### Average Per Run

- **Average Cost per Run**: $0.064286
- **Average Tokens per Run**: 50125.2
  - Prompt Tokens: 10902.0
  - Completion Tokens: 39223.2
