from llmp.components.base import BaseEvaluationEngine
from llmp.data_model import JobRecord, ExampleRecord
from llmp.components.generator import SequentialAsyncGenerator
from llmp.data_model.events import Event
from llmp.types import GenOutput
import llmp.components.evaluation.metrics as metrics


class EvaluationEngine(BaseEvaluationEngine):
    """
    The EvaluationEngine is responsible for evaluating the generated examples
    and updating the job accordingly.
    """

    def __init__(self, job: JobRecord, num_runs: int = 5):
        """Initialize the EvaluationEngine with a job and job settings.

        Args:
            job: JobRecord
            num_runs: int
        """
        super().__init__(job)
        self._num_runs = num_runs

    def evaluate(self, records: list[ExampleRecord], job_settings: dict = None):
        """Evaluate the generated examples for a specific job."""
        generator = SequentialAsyncGenerator(self.job, job_settings, self._num_runs)

        # generate outputs
        results = generator.generate(input_data=[record.input for record in records])
        assert len(results) == len(records)

        sample_metrics = []
        for outputs_metrics, sample_record in zip(results, records):
            sample_metric = self.compute_sample_metrics(outputs_metrics, sample_record.output, sample_record.input)

            sample_metrics.append(sample_metric)
            self.job.log_event(
                Event.from_sample_metric(sample_metric, job_settings, example_id=sample_record.idx)
            )

        aggregated_metrics = self.compute_metrics(sample_metrics)

        self.job.log_event(
            Event.from_evaluation_metric(aggregated_metrics, job_settings, example_ids=[r.idx for r in records])
        )
        return aggregated_metrics

    def compute_sample_metrics(self, outputs_metrics: list[GenOutput], ideal_output: dict, sample_input: dict) -> dict:
        """Compute metrics for a single generation sample from multiple runs."""

        # unpack outputs and metrics
        outputs, run_metrics = [o for o, _ in outputs_metrics], [m for _, m in outputs_metrics]

        # Compute accuracy
        if self.job.is_explicit:
            accuracy_metrics = metrics.explicit_accuracy(outputs, ideal_output)
        else:
            accuracy_metrics = metrics.implicit_accuracy(outputs, ideal_output, self.job, sample_input)

        # Aggregate metrics
        return {
            "accuracy": accuracy_metrics,
            "execution_time": metrics.avg_efficiency(run_metrics),
            "failure_rate": metrics.avg_failure_rate(run_metrics),
            "token_usage": metrics.avg_token_usage(run_metrics),
            "num_runs": len(run_metrics),
            "model_name": run_metrics[0]["model_name"],
            "model_config": run_metrics[0]["model_config"],
            "errors": [e for m in run_metrics for e in m["errors"] if m["errors"] is not None]
        }

    def compute_metrics(self, sample_metrics: list[dict]) -> dict:
        """Compute metrics for a single generation sample from multiple runs."""
        return {
            "accuracy": metrics.avg_accuracy(sample_metrics),
            "execution_time": metrics.avg_efficiency(sample_metrics),
            "failure_rate": metrics.avg_failure_rate(sample_metrics),
            "token_usage": metrics.avg_token_usage(sample_metrics),
            "num_runs": metrics.avg_num_runs(sample_metrics),
            "model_name": sample_metrics[0]["model_name"],
            "model_config": sample_metrics[0]["model_config"],
            "errors": [e for m in sample_metrics for e in m["errors"] if m["errors"] is not None]
        }
