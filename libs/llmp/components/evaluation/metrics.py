from llmp.data_model import JobRecord
from llmp.components.evaluation.prompts import MATCH_RESPONSE
from llmp.integration.structgenie import Engine


def explicit_accuracy(outputs: list, ideal_output: dict):
    """Compute the accuracy of the outputs."""
    correct = 0
    for output in outputs:
        if output == ideal_output:
            correct += 1
    return correct / len(outputs)


def implicit_accuracy(outputs: list, ideal_output: dict, job: JobRecord, sample_input: dict):
    """Compute the accuracy of the outputs."""
    correct = 0
    engine = Engine.from_template(MATCH_RESPONSE)
    for output in outputs:
        input_data = {
            "instruction": job.instruction,
            "ideal_output": ideal_output,
            "output": output,
            "example_input": sample_input,
        }
        output = engine.run(input_data)
        if not output["choice"] == "D":
            correct += 1
    return correct / len(outputs)



def avg_accuracy(run_metrics: list[dict]):
    """Compute the average accuracy of the runs."""
    return sum([m["accuracy"] for m in run_metrics]) / len(run_metrics)


def avg_efficiency(run_metrics: list[dict]):
    """Compute the average efficiency of the runs."""
    return sum([m["execution_time"] for m in run_metrics]) / len(run_metrics)


def avg_failure_rate(run_metrics):
    """Compute the average failure rate of the runs."""
    return sum([m["failure_rate"] for m in run_metrics]) / len(run_metrics)


def avg_token_usage(outputs):
    """Compute the average token usage of the outputs."""
    return sum([m["token_usage"] for m in outputs]) / len(outputs)


def avg_num_runs(outputs):
    """Compute the average number of runs."""
    return sum([m["num_runs"] for m in outputs]) / len(outputs)
