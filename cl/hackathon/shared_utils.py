from typing import Any
import numpy as np
import pandas as pd

AGREEMENT_THRESHOLD = 0.5


def manage_results(results_list: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Manage conflicts from different results from calling the LLM.
    :param results_list: a list of results of multiple runs (e.g. list of json outputs)
    :return: a single json_output
    """
    df = pd.DataFrame(results_list)

    # get most common results
    modal_results = df.mode(dropna=False).iloc[0].dropna()

    # make sure each results has agreement above AGREEMENT_THRESHOLD
    for key, val in modal_results.items():
        count = sum(df[key] == val)
        if count / len(df) < AGREEMENT_THRESHOLD:
            modal_results[key] = np.nan

    modal_results.dropna(inplace=True)
    json_output = modal_results.to_dict()
    return json_output


if __name__ == "__main__":
    dummy_list = [
        {"label_a": "a", "label_b": 2, "label_c": 1, "label_d": 10, "label_e": 1},
        {"label_a": "a", "label_b": 1, "label_c": 2},
        {"label_a": "a", "label_b": 1, "label_c": 3, "label_d": 10},
        {"label_a": "a", "label_b": 1, "label_c": 4},
        {"label_a": "b", "label_b": 1, "label_c": 5, "label_d": 10},
    ]
    res = manage_results(dummy_list)
    print(res)
