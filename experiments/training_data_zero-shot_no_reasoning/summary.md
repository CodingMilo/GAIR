# Model Comparison Report
Generated: 2026-03-03 23:52:57

## Configuration

- **Models Tested**: 8
- **Repetitions**: 5
- **Temperature**: 1.0
- **Max Reasoning Tokens**: 0
- **Dataset**: ../../train.csv
- **Message**: Batch comparison

## Results Summary

| Rank | Model | Accuracy | Kaggle Score | Total Cost ($) | Total Tokens | Avg Cost/Run ($) | Avg Tokens/Run | Cost per 1% Acc ($) | Duration |
|------|-------|----------|--------------|----------------|--------------|------------------|----------------|---------------------|----------|
| 1 | google-gemini-3-flash-preview | 0.6776 ± 0.0396 | 0.6766 | $0.0304 | 52,716 | $0.006089 | 10543.2 | N/A | 0:00:56.317216s |
| 2 | qwen-qwen3-235b-a22b-2507 | 0.5959 ± 0.0271 | 0.5957 | $0.0078 | 66,420 | $0.001556 | 13284.0 | N/A | 0:16:06.670007s |
| 3 | qwen-qwen3-5-plus-02-15 | 0.5837 ± 0.0208 | 0.5829 | $0.0259 | 56,557 | $0.005189 | 11311.4 | N/A | 0:01:09.870817s |
| 4 | z-ai-glm-4-7 | 0.5347 ± 0.0200 | 0.5342 | $0.0164 | 53,148 | $0.003269 | 10582.6 | N/A | 0:01:43.421411s |
| 5 | deepseek-deepseek-v3-2 | 0.5265 ± 0.0396 | 0.5261 | $0.0138 | 52,740 | $0.002752 | 10548.0 | N/A | 0:02:18.396422s |
| 6 | x-ai-grok-4-1-fast | 0.5143 ± 0.0300 | 0.5141 | $0.0075 | 89,328 | $0.001506 | 17865.6 | N/A | 0:00:49.313937s |
| 7 | openai-gpt-4-1-mini | 0.4490 ± 0.0387 | 0.4483 | $0.0239 | 53,413 | $0.004780 | 10682.6 | N/A | 0:00:44.516851s |
| 8 | minimax-minimax-m2-1 | N/A | 0.0000 | N/A | N/A | N/A | N/A | N/A | 0:00:06.114048s |
