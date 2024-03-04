"""
Job Presentation Layer

This layer is responsible for presenting the job to the user.
We want to achieve a simple and intuitive interface for the user to interact with the job.
The initialization of the job should be done with providing an input and output model to the job constructor.
When no input/output model is provided, the job is supposed to be loaded from the database.

The process of a new job creation should be as follows:
1. The user provides an input and output model to the job constructor.
2. The job constructor creates a new job in the database.
3. The job constructor generates an instruction for the job.
---
With that the job is ready to be used as a zero-shot model.
The user can now provide an input to the job and receive an output.
With our first output we can now start the optimization process.
The optimization process is supposed to be done in the background if mode is set to auto:
1. The user provides an input to the job.
2. The job constructor generates an output for the input.
3. Here we have several options:
    a. We generate an output for the job and regard it as a reliable example.
    b. We set a mandatory User Interaction to verify the output as default.
    c. We run an MajorVoteGenerator to generate a new output via consensus.


Handle Settings:
We can pass a settings object to the program constructor. If no settings object is provided, we load the settings from global singleton
A program specific settings object will also load all unset options from the global settings object.
When calling a program we can pass kwargs to overwrite the settings object on the run.

Parameters
----------
signature : str
    The signature of the job.
input_model : Type[BaseModel]
    The input model of the job.
output_model : Type[BaseModel]
    The output model of the job.
config : dict
    The configuration of the job.


"""
from structgenie.pydantic_v1 import BaseModel
from typing import Type

from llmp.utils.signature import is_valid_uuid

from llmp.components.settings.program_settings import ProgramSettings, PromptType
from llmp.data_model import JobRecord
from llmp.services.job_manager import JobManager
from llmp.utils.helper import dotdict
from llmp.types import IOModelDefinition


class Program:
    """
    The Program class is responsible for managing a job. It provides an interface for the user to interact with the job.
    The job can be initialized by providing an input and output model to the job constructor. If no input/output model is provided, the job is loaded from the database.

    Attributes:
        job (JobRecord): The job record associated with the Program instance.

    Methods:
        __init__(self, signature: str, input_model: IOModelDefinition = None, output_model: IOModelDefinition = None, config: ProgramSettings = ProgramSettings(), load_if_exist: bool = True, **kwargs): Initializes a Program instance.
        __call__(self, input_data: dict, auto_optimize: bool = True, log_action: bool = True, return_metrics: bool = False, **kwargs): Generates output for a specific input.
        _load_by_signature(self, signature: str): Attempts to load a job by its signature.
        _load_by_io_model(self, input_model: IOModelDefinition, output_model: IOModelDefinition, instruction: str = None): Attempts to load a job by its input and output model.
        event_log(self): Returns the event log of the job.
        generation_log(self): Returns the generation log of the job.
    """

    job: JobRecord

    def __init__(
            self,
            signature: str,
            input_model: IOModelDefinition = None,
            output_model: IOModelDefinition = None,
            config: ProgramSettings = ProgramSettings(),
            load_if_exist: bool = True,
            **kwargs):
        """
        Initializes a Program instance.

        Args:
            signature (str): The signature of the job.
            input_model (IOModelDefinition, optional): The input model of the job. Defaults to None.
            output_model (IOModelDefinition, optional): The output model of the job. Defaults to None.
            config (ProgramSettings, optional): The configuration of the job. Defaults to ProgramSettings().
            load_if_exist (bool, optional): If True, attempts to load a job if it exists. Defaults to True.
            **kwargs: Additional keyword arguments.
        """
        self.job_manager = JobManager(config.base_path)
        self.config = config

        # if input_model/output_model create new Job
        if load_if_exist:
            if self._load_by_signature(signature):
                return
            if self._load_by_io_model(input_model, output_model, instruction=kwargs.get("instruction", None)):
                return

        if input_model and output_model:
            self.job = self.job_manager.create_job(
                signature,
                input_model=input_model,
                output_model=output_model,
                config=config.dict(),
                **kwargs
            )
        # load job by signature
        else:
            self.job = self.job_manager.get_job(signature)

    def __call__(
            self,
            input_data: dict,
            auto_optimize: bool = True,
            log_action: bool = True,
            return_metrics: bool = False,
            **kwargs):
        """Generate output for a specific input.

        When called, the job will generate an output for the provided input.

        """
        is_first_run = False
        generator_type = self.config.generator_type
        if len(self.job.example_records) == 0 and not self.config.program_type == PromptType.ZERO_SHOT:
            is_first_run = True
            generator_type = "consensus"

        output, run_metrics = self.job_manager.generate_output(
            self.job, input_data, generator_type=generator_type, **kwargs
        )

        if is_first_run:
            self.job_manager.optimize_job(self.job, mode="all")

        dotdict_output = dotdict(output)
        if return_metrics:
            dotdict_output.run_metrics = run_metrics
        return dotdict_output

    def _load_by_signature(self, signature: str):
        try:
            if is_valid_uuid(signature):
                self.job = self.job_manager.get_job(idx=signature)
            else:
                self.job = self.job_manager.get_job(name=signature)
            return True
        except:
            return False

    def _load_by_io_model(self, input_model: IOModelDefinition, output_model: IOModelDefinition, instruction: str = None):
        try:
            self.job = self.job_manager.get_job_by_input_output_model(
                input_model, output_model, instruction=instruction, config=self.config.dict()
            )
            return True
        except:
            return False

    def event_log(self):
        return self.job_manager.get_event_log(self.job.idx)

    def generation_log(self):
        return self.job_manager.get_generation_log(self.job.idx)
