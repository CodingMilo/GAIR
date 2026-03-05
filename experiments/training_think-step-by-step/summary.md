# Model Comparison Report
Generated: 2026-03-05 00:48:11

## Configuration

- **Models Tested**: 7
- **Repetitions**: 5
- **Temperature**: 1.0
- **Max Reasoning Tokens**: 0
- **Dataset**: C:\Users\zzg_s\OneDrive - CentraleSupelec\Code\Python\scripts_gair_2026\experiments\train.csv
- **Message**: Batch comparison

## Results Summary

| Rank | Model | Accuracy | Kaggle Score | Total Cost ($) | Total Tokens | Avg Cost/Run ($) | Avg Tokens/Run | Cost per 1% Acc ($) | Duration |
|------|-------|----------|--------------|----------------|--------------|------------------|----------------|---------------------|----------|
| 1 | google-gemini-3-flash-preview_20260304_233153 | 0.8449 ± 0.0100 | 0.8314 | $0.4506 | 195,406 | $0.090113 | 39081.2 | $0.1067 | 0:09:30.785755s |
| 2 | qwen-qwen3-235b-a22b-2507_20260304_233153 | 0.8204 ± 0.0327 | 0.8134 | $0.2325 | 521,273 | $0.046502 | 104254.6 | $0.0567 | 0:46:49.028160s |
| 3 | deepseek-deepseek-v3.2_20260304_233153 | 0.7918 ± 0.0153 | 0.7876 | $0.1409 | 315,421 | $0.028188 | 63084.2 | $0.0356 | 0:48:20.704222s |
| 4 | mistralai-mistral-large-2512_20260304_233153 | 0.7429 ± 0.0208 | 0.7332 | $0.3214 | 250,626 | $0.064286 | 50125.2 | $0.0865 | 0:12:21.524818s |
| 5 | openai-gpt-4.1-mini_20260304_233153 | 0.6980 ± 0.0327 | 0.6872 | $0.3579 | 263,464 | $0.071585 | 52692.8 | $0.1026 | 0:10:47.457062s |
| 6 | x-ai-grok-4.1-fast_20260304_233153 | 0.6122 ± 0.0224 | 0.6090 | $0.1098 | 297,197 | $0.021953 | 59439.4 | $0.0359 | 0:10:23.272471s |
| 7 | openai-gpt-5-mini_20260304_233153 | N/A | 0.0000 | N/A | N/A | N/A | N/A | N/A | 0:06:44.818888s |
