from typing import Tuple

from llmp.components.evaluation import metrics
from llmp.components.generator._prompts import FIND_BEST_TEMPLATE
from llmp.data_model import JobRecord
from llmp.integration.structgenie import Engine


def get_majority_vote(outputs: list[Tuple[dict, dict]], min_votes: int = 2, job: JobRecord = None) -> Tuple[dict, dict]:
    """Returns the consensus and share of votes output from a list of outputs."""
    merged_metrics = _merge_metrics([m for _, m in outputs])
    outputs = [o for o, _ in outputs]
    ranked_outputs = _rank_outputs(outputs)
    try:
        if ranked_outputs[0][1] >= min_votes:
            merged_metrics["reliability"] = ranked_outputs[0][1] / len(outputs)
            return ranked_outputs[0][0], merged_metrics
        else:
            merged_metrics["reliability"] = 0.9
            return get_best_output(outputs, job), merged_metrics
    except IndexError:
        print("Index Error")
        print(ranked_outputs)
        print(ranked_outputs[0][1])


def get_best_output(outputs: list[dict], job: JobRecord) -> dict:

    unique_outputs = _get_unique_outputs(outputs)
    st = Engine.from_template(FIND_BEST_TEMPLATE)
    inputs = {
        "task_instruction": job.instruction,
        "task_input": {'description': 'A social media marketing campaign to be created',
                       'sources': ['internal', 'external']},
        "task_output": [{f"Output {i}": o} for i, o in enumerate(unique_outputs)],
    }
    best_option = st.generate(inputs)
    return unique_outputs[int(best_option["index"])]


def get_majority_grade(outputs: list[tuple[dict, dict]], job: JobRecord) -> Tuple[dict, dict]:
    """Returns the grading output from a list of outputs."""
    merged_metrics = _merge_metrics([m for _, m in outputs])
    outputs = [o for o, _ in outputs]
    merged_metrics["reliability"] = 0.9
    return get_best_output(outputs, job), merged_metrics


def get_human_vote(outputs: list[tuple[dict, dict]]) -> dict:
    """Returns the human verified output from a list of outputs."""
    return NotImplemented


def remove_reasoning(data: dict):
    for key in ["reason", "chain-of-thoughts", "reasoning"]:
        if key in data:
            del data[key]
    return data


def _count_outputs(outputs: list[dict]) -> list[tuple[dict, int]]:
    options = {}
    option_index_list = []
    option_index_clean_list = []

    for output in outputs:
        clean_output = remove_reasoning(output.copy())
        if clean_output in option_index_clean_list:
            # get index
            index = option_index_clean_list.index(clean_output)
            options[index] += 1
        else:
            option_index_list.append(output)
            option_index_clean_list.append(clean_output)
            options[option_index_list.index(output)] = 1
    return [(option_index_list[i], options[i]) for i in range(len(option_index_list))]


def _rank_outputs(outputs: list[dict]) -> list[tuple[dict, int]]:
    """Ranks outputs by the number of times they appear in the outputs list."""
    return _sort_count(_count_outputs(outputs))


def _sort_count(tuple_list: list[tuple[dict, int]]) -> list[tuple[dict, int]]:
    """Sorts a list of tuples by the second value in the tuple, in descending order."""
    return sorted(tuple_list, key=lambda x: x[-1], reverse=True)


def _merge_metrics(run_metrics: list[dict]) -> dict:
    """Merge a list of metrics into a single metric."""
    return {
        "execution_time": metrics.avg_efficiency(run_metrics),
        "failure_rate": metrics.avg_failure_rate(run_metrics),
        "token_usage": metrics.avg_token_usage(run_metrics),
        "num_runs": len(run_metrics),
        "model_name": run_metrics[0]["model_name"],
        "model_config": run_metrics[0]["model_name"],
        "errors": [e for m in run_metrics for e in m["errors"] if m["errors"] is not None]
    }


def _get_unique_outputs(outputs: list[dict]) -> list[dict]:
    unique_outputs = []
    for o in outputs:
        if o[0] not in unique_outputs:
            unique_outputs.append(o[0])
    return unique_outputs


# === unused ===


def get_majority_vote_by_key(outputs: list[Tuple[dict, dict]]) -> Tuple[dict, dict]:
    """Returns the consensus for each key from a list of outputs.

    Select the best output for each key based on the number of votes.
    """
    outputs, run_metrics = (list(i) for i in zip(*outputs))
    composed_output = {key: _rank_outputs_by_key(outputs, key)[0][key] for key in outputs[0].keys()}
    avg_votes = sum(
        [_rank_outputs_by_key(outputs, key)[0][1] for key in outputs[0].keys()]
    ) / len(outputs[0][0].keys())

    merged_metric = {
            "reliability": avg_votes / len(outputs),
            "execution_time": metrics.avg_efficiency(run_metrics),
            "failure_rate": metrics.avg_failure_rate(run_metrics),
            "token_usage": metrics.avg_token_usage(run_metrics),
            "num_runs": len(run_metrics),
            "llm_model": run_metrics[0]["llm_model"],
            "llm_config": run_metrics[0]["llm_config"],
            "errors": [e for m in run_metrics for e in m["errors"] if m["errors"] is not None]
        }

    return composed_output, merged_metric


def _rank_outputs_by_key(outputs: list[dict], key: str) -> list[tuple[dict, int]]:
    """Ranks output keys by the number of times they appear in the outputs list."""
    return _sort_count(_count_output_values_by_key(outputs, key))


def _count_output_values_by_key(outputs: list[dict], key: str) -> list[tuple[dict, int]]:
    options = {}
    for output in outputs:
        value = str(output[key])
        if value in options:
            options[value]["count"] += 1
        else:
            options[value] = {}
            options[value]["count"] = 1
            options[value]["value"] = output
    return [(options[option]["value"], options[option]["count"]) for option in options]
