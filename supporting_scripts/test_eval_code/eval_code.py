"""
Average kaggle score over five predictions.
"""

import pandas as pd
import pandas.api.types
from sklearn.metrics import accuracy_score
import numpy as np


class ParticipantVisibleError(Exception):
    # If you want an error message to be shown to participants, you must raise the error as a ParticipantVisibleError
    # All other errors will only be shown to the competition host. This helps prevent unintentional leakage of solution data.
    pass

# Define the scoring function
def calculate_kaggle_score(acc, cost):
    if cost > 0.3:
        return 0.0
    else:
        kaggle_score_base = acc-.15*cost
        kaggle_score = min(kaggle_score_base, 1.0)
        kaggle_score = max(kaggle_score, 0)
        return kaggle_score


def score(solution: pd.DataFrame, submission: pd.DataFrame, row_id_column_name: str, min_predictions: int = 1) -> float:
    '''
    >>> import pandas as pd
    >>> num_rows = 5
    >>> data = {'question_id': list(range(num_rows))}
    >>> submission = pd.DataFrame(data)
    >>> for i in range(1, 6):
    ...     column_name = f'prediction_{i}'
    ...     submission[column_name] = ['a']*num_rows
    >>> solution = pd.DataFrame(data)
    >>> solution['answer'] = ['a']*num_rows
    >>> submission.loc[:, 'Average cost per run'] = 1
    >>> _ = score(solution.copy(), submission.copy(), 'question_id')
    Mean accuracy (5 predictions): 1.0
    '''

    if row_id_column_name in solution.columns:
        del solution[row_id_column_name]
    else:
        raise ParticipantVisibleError(f"solution.csv must have a column named {row_id_column_name}.")
    
    if not 'Average cost per run' in submission.columns:
        raise ParticipantVisibleError("submission.csv must have a column named 'Average cost per run'.")
    else:
        avg_cost_per_run = submission['Average cost per run'].mean()
        del submission['Average cost per run']
    
    if row_id_column_name in submission.columns:
        del submission[row_id_column_name]
    else:
        raise ParticipantVisibleError(f"submission.csv must have a column named {row_id_column_name}.")

    results = []
    num_predictions = submission.shape[1]
    
    if num_predictions < min_predictions:
        raise ParticipantVisibleError(f"submission.csv must have at least {min_predictions} prediction column(s), but has {num_predictions} columns.")
    

    y_true = solution['answer']
    for i in range(num_predictions):
        y_pred = submission.iloc[:, i]
        # Replace all the nan values in y_pred with string 'nan'
        y_pred = y_pred.fillna('nan')
        result = accuracy_score(y_true, y_pred)
        results.append(result)

        # print(y_true.loc[y_true!=y_pred])
        # print(y_pred.loc[y_true!=y_pred])

    mean_acc = np.mean(results)
    
    print(f'Mean accuracy ({num_predictions} predictions): {mean_acc}')

    kaggle_score = calculate_kaggle_score(mean_acc, avg_cost_per_run)

    return kaggle_score


if __name__ == '__main__':
    solution_path = "C:/Users/zzg_s/OneDrive - CentraleSupelec/Code/Python/llm_reliability_engineering/eval_baseline/create_dataset_data_challenge_2026/dataset_kaggle_mcq/solution.csv"
    submission_path = "C:/Users/zzg_s/OneDrive - CentraleSupelec/Code/Python/scripts_gair_2026/experiments/test_data/mistralai-mistral-large-2512_20260305_084113/solution_kaggle.csv"

    solution = pd.read_csv(solution_path)
    submission = pd.read_csv(submission_path)

    solution_public = solution[solution['Usage']=='Public']
    solution_private = solution[solution['Usage']=='Private']
    submission_public = submission[solution['Usage']=='Public']
    submission_private = submission[solution['Usage']=='Private']

    print(f'Kaggle score (Public): {score(solution_public, submission_public, 'question_id')}')
    print(f'Kaggle score (Private): {score(solution_private, submission_private, 'question_id')}')
    