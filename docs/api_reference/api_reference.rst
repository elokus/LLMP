.. _api_reference:

=======================
``llmp`` API Reference
=======================

:mod:`llmp.components`
=======================

.. automodule:: llmp.components
    :no-members:
    :no-inherited-members:

Classes
--------------
.. currentmodule:: llmp

.. autosummary::
    :toctree: components
    :template: class.rst

    components.base.BaseEvaluationEngine

    :template: class.rst

    components.base.BaseExampleManager

    :template: class.rst

    components.base.BaseGenerator

    :template: class.rst

    components.base.BaseHumanVerification

    :template: class.rst

    components.base.BaseInstructionHandler

    :template: class.rst

    components.base.BaseOptimizer

    :template: class.rst

    components.evaluation.engine.EvaluationEngine

    :template: class.rst

    components.example_manager.ExampleManager

    :template: class.rst

    components.generator.concurrent.AsyncGenerator

    :template: class.rst

    components.generator.concurrent.MultiThreadingAsyncGenerator

    :template: class.rst

    components.generator.concurrent.SequentialAsyncGenerator

    :template: class.rst

    components.generator.concurrent.SequentialAsyncGenerator2

    :template: class.rst

    components.generator.consensus.MajorVoteGenerator

    :template: class.rst

    components.generator.examples.ExampleGenerator

    :template: class.rst

    components.generator.simple.Generator

    :template: class.rst

    components.human_verification.HumanVerification

    :template: class.rst

    components.instruction.generation.InstructionGenerator

    :template: class.rst

    components.instruction.mutation.InstructionMutation

    :template: class.rst

    components.job_factory.ExampleJobCreator

    :template: class.rst

    components.job_factory.JobCreator

    :template: class.rst

    components.job_factory.ModelJobCreator

    :template: class.rst

    components.job_factory.TemplateJobCreator

    :template: class.rst

    components.optimizer.examples.ExampleOptimizer

    :template: class.rst

    components.optimizer.instructions.InstructionOptimizer

    :template: class.rst

    components.optimizer.optimizer.Optimizer

    :template: class.rst

    components.settings.global_settings.GlobalSettings

    :template: pydantic.rst

    components.settings.program_settings.ProgramSettings

    :template: enum.rst

    components.settings.program_settings.PromptType

Functions
--------------
.. currentmodule:: llmp

.. autosummary::
    :toctree: components
    :template: function.rst

    components.evaluation.metrics.avg_accuracy
    components.evaluation.metrics.avg_efficiency
    components.evaluation.metrics.avg_failure_rate
    components.evaluation.metrics.avg_num_runs
    components.evaluation.metrics.avg_token_usage
    components.evaluation.metrics.explicit_accuracy
    components.evaluation.metrics.implicit_accuracy
    components.generator.verification.get_best_output
    components.generator.verification.get_human_vote
    components.generator.verification.get_majority_grade
    components.generator.verification.get_majority_vote
    components.generator.verification.get_majority_vote_by_key
    components.generator.verification.remove_reasoning
    components.instruction.utils.extend_instruction_by_example
    components.instruction.utils.extend_instruction_by_model
    components.instruction.utils.generate_instruction_from_model_and_template
    components.instruction.utils.generate_instruction_from_models
    components.instruction.utils.instruction_from_working_out
    components.instruction.utils.mutate_instruction
    components.job_factory.job_factory

:mod:`llmp.components.evaluation`
==================================

.. automodule:: llmp.components.evaluation
    :no-members:
    :no-inherited-members:

Classes
--------------
.. currentmodule:: llmp

.. autosummary::
    :toctree: components.evaluation
    :template: class.rst

    components.evaluation.engine.EvaluationEngine

Functions
--------------
.. currentmodule:: llmp

.. autosummary::
    :toctree: components.evaluation
    :template: function.rst

    components.evaluation.metrics.avg_accuracy
    components.evaluation.metrics.avg_efficiency
    components.evaluation.metrics.avg_failure_rate
    components.evaluation.metrics.avg_num_runs
    components.evaluation.metrics.avg_token_usage
    components.evaluation.metrics.explicit_accuracy
    components.evaluation.metrics.implicit_accuracy

:mod:`llmp.components.example_manager`
=======================================

.. automodule:: llmp.components.example_manager
    :no-members:
    :no-inherited-members:

Classes
--------------
.. currentmodule:: llmp

.. autosummary::
    :toctree: components.example_manager
    :template: class.rst

    components.example_manager.ExampleManager

:mod:`llmp.components.generator`
=================================

.. automodule:: llmp.components.generator
    :no-members:
    :no-inherited-members:

Classes
--------------
.. currentmodule:: llmp

.. autosummary::
    :toctree: components.generator
    :template: class.rst

    components.generator.concurrent.AsyncGenerator

    :template: class.rst

    components.generator.concurrent.MultiThreadingAsyncGenerator

    :template: class.rst

    components.generator.concurrent.SequentialAsyncGenerator

    :template: class.rst

    components.generator.concurrent.SequentialAsyncGenerator2

    :template: class.rst

    components.generator.consensus.MajorVoteGenerator

    :template: class.rst

    components.generator.examples.ExampleGenerator

    :template: class.rst

    components.generator.simple.Generator

Functions
--------------
.. currentmodule:: llmp

.. autosummary::
    :toctree: components.generator
    :template: function.rst

    components.generator.verification.get_best_output
    components.generator.verification.get_human_vote
    components.generator.verification.get_majority_grade
    components.generator.verification.get_majority_vote
    components.generator.verification.get_majority_vote_by_key
    components.generator.verification.remove_reasoning

:mod:`llmp.components.optimizer`
=================================

.. automodule:: llmp.components.optimizer
    :no-members:
    :no-inherited-members:

Classes
--------------
.. currentmodule:: llmp

.. autosummary::
    :toctree: components.optimizer
    :template: class.rst

    components.optimizer.examples.ExampleOptimizer

    :template: class.rst

    components.optimizer.instructions.InstructionOptimizer

    :template: class.rst

    components.optimizer.optimizer.Optimizer

:mod:`llmp.data_model`
=======================

.. automodule:: llmp.data_model
    :no-members:
    :no-inherited-members:

Classes
--------------
.. currentmodule:: llmp

.. autosummary::
    :toctree: data_model
    :template: pydantic.rst

    data_model.events.Event

    :template: pydantic.rst

    data_model.example_record.ExampleRecord

    :template: pydantic.rst

    data_model.job_record.JobRecord

Functions
--------------
.. currentmodule:: llmp

.. autosummary::
    :toctree: data_model
    :template: function.rst

    data_model.job_record.get_record_by_input
    data_model.job_record.get_template_from_job
    data_model.job_record.input_in_records
    data_model.job_record.load_engine_from_job

:mod:`llmp.integration`
========================

.. automodule:: llmp.integration
    :no-members:
    :no-inherited-members:

Classes
--------------
.. currentmodule:: llmp

.. autosummary::
    :toctree: integration
    :template: pydantic.rst

    integration.example_selector.ExampleManagerSelector

:mod:`llmp.services`
=====================

.. automodule:: llmp.services
    :no-members:
    :no-inherited-members:

Classes
--------------
.. currentmodule:: llmp

.. autosummary::
    :toctree: services
    :template: class.rst

    services.job_manager.JobManager

    :template: class.rst

    services.job_storage.JobStorage

    :template: class.rst

    services.program.Program

Functions
--------------
.. currentmodule:: llmp

.. autosummary::
    :toctree: services
    :template: function.rst

    services.job_manager.load_generator_cls

:mod:`llmp.tests`
==================

.. automodule:: llmp.tests
    :no-members:
    :no-inherited-members:

Functions
--------------
.. currentmodule:: llmp

.. autosummary::
    :toctree: tests
    :template: function.rst

    tests.resources.fixtures.create_job_input
    tests.resources.fixtures.job_id
    tests.resources.fixtures.job_manager
    tests.resources.fixtures.temp_job_id
    tests.resources.fixtures.test_job
    tests.resources.fixtures.test_output_concensus_generator
    tests.test_basic_fn.test_tuple_list_unpacking
    tests.test_example_generator.test_fill_examples
    tests.test_example_generator.test_job
    tests.test_job_manager.test_delete_job
    tests.test_job_manager.test_job_creation
    tests.test_job_manager.test_job_loading
    tests.test_job_manager.test_update_job
    tests.test_job_record.input_example
    tests.test_job_record.test_example_in_job
    tests.test_job_record.test_record_by_input
    tests.test_job_storing_logging.test_event_log_adding
    tests.test_job_storing_logging.test_job_event_log_loading

:mod:`llmp.types`
==================

.. automodule:: llmp.types
    :no-members:
    :no-inherited-members:

Classes
--------------
.. currentmodule:: llmp

.. autosummary::
    :toctree: types
    :template: enum.rst

    types.EventType

    :template: enum.rst

    types.MajorVoteType

    :template: enum.rst

    types.TestSetMode

    :template: enum.rst

    types.VerificationType

:mod:`llmp.utils`
==================

.. automodule:: llmp.utils
    :no-members:
    :no-inherited-members:

Classes
--------------
.. currentmodule:: llmp

.. autosummary::
    :toctree: utils
    :template: class.rst

    utils.encoder.JSONEncoder

    :template: class.rst

    utils.helper.dotdict

    :template: class.rst

    utils.singleton.Singleton

Functions
--------------
.. currentmodule:: llmp

.. autosummary::
    :toctree: utils
    :template: function.rst

    utils.encoder.dumps_encoder
    utils.eval.f1_score
    utils.eval.fuzzy_match
    utils.eval.get_consensus
    utils.eval.normalize
    utils.helper.flatten
    utils.helper.get_timestamp
    utils.helper.int_or_float
    utils.helper.safe_getter
    utils.helper.update_by_kwargs
    utils.signature.is_valid_uuid
    utils.signature.safe_job_name

