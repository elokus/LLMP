from typing import Callable, Type, Optional
import re
import colorama
from colorama import Fore

from llmp.data_model import JobRecord
from llmp.pydantic_v1 import BaseModel, Field
from llmp.services.job_manager import JobManager


class AssignTaskSchema(BaseModel):
    name: str
    instruction: str


class SingleToolInput(BaseModel):
    instruction: str


class CheckInputDataInput(BaseModel):
    instruction: str
    parameter: str


class CheckInputDataOutput(BaseModel):
    information_sufficient: bool
    missing_parameters: Optional[list]
    reason: Optional[str]


class AgentResponse(BaseModel):
    content: str
    success: bool
    metrics: Optional[dict] = None

def agent_name_from_tool(tool: Callable):
    return tool.__name__



def parse_docstring(docstring: str) -> dict:
    """Parse a docstring into its components.

    Args:
        docstring (str): The docstring to parse.

    Returns:
        dict: The parsed docstring. The keys are "short_description", "args", and "returns".
    """
    # Split the docstring into its components
    parts = re.split(r"\n\s*\n", docstring.strip(), maxsplit=3)

    # Extract the short description
    short_description = parts[0].strip()

    # Extract the arguments and return value
    if len(parts) == 1:
        return {
            "short_description": short_description,
            "args": [],
            "returns": []
        }
    else:
        try:
            if "Args:" in parts[1]:
                args = re.findall(r"(\w+) \((.*)\): (.+)", parts[1])
            else:
                args = []
        except:
            args = []

        try:
            returns = re.findall(r"Returns:\n\s*(\w+): (.+)", parts[2])
        except:
            returns = []

    # Return the parsed docstring
    return {
        "short_description": short_description,
        "args": args,
        "returns": returns
    }

INSTRUCTION = """You are a Software Operator. Your job is to run a software tool on a given input.
To do this, you will need to prepare the parameter. 
Extract or derive the input from the instruction and prepare the parameter according to the format instruction below.
Some parameters might be implicit in the instruction or hidden in the context of the instruction.
You should be able to derive or calculate all parameters from the instruction.
"""

INSTRUCTION_CHECK = """Verify if the input instruction is sufficient to derive or extract the required parameters.
The parameter might be implicit in the instruction or hidden in the context of the instruction. 
When you are able to deduce/derive the parameters from the instruction, return True.
The information are also sufficient if you are able to calculate or generate the missing parameter, truthfully.
The information must not be explicitly mentioned!
If not, return information_sufficient as false and list missing parameters.
Do only list the missing parameters that can not be derived from the instruction and are not optional.

Before you not approve sufficiency, you should think step by step if you can derive the parameters from the instruction.
Explain your decision in the reason field and also mention which information you can derive by your own capabilities and which not.
"""


METRIC_DEFAULT = {
    "execution_time": 0,
    "token_usage": 0,
    "model_name": None,
    "model_config": {},
    "errors": []
}

class SingleToolAgent(BaseModel):

    name: str
    description: str
    tool: Callable
    job: JobRecord
    check_job: JobRecord
    job_manager: JobManager
    verbose: int = 0
    metrics: dict = METRIC_DEFAULT


    class Config:
        arbitrary_types_allowed = True


    @classmethod
    def prepare_job(
            cls,
            tool: Callable,
            arg_schema: Type[BaseModel],
            input_model: Type[BaseModel] = SingleToolInput,
            job_manager: JobManager = JobManager(),
            **kwargs
    ):

        instruction = kwargs.get("instruction", INSTRUCTION)
        name = kwargs.get("name", tool.__name__)
        description = kwargs.get("description", parse_docstring(tool.__doc__)["short_description"])

        for key in ["instruction", "name", "description"]:
            if key in kwargs:
                del kwargs[key]

        job = job_manager.create_job(
            job_name=tool.__name__,
            input_model=input_model,
            output_model=arg_schema,
            instruction=instruction,
            **kwargs
        )
        examples = [
            (
                CheckInputDataInput(
                    instruction="Track my sports activities. I have run 5 km in 25 minutes today.",
                    parameter="distance_run: int, time: int, speed: float, date: datetime.datetime"
                ),
                CheckInputDataOutput(
                    information_sufficient=False,
                    missing_parameters=["date"],
                    reason="Only distance and time are given. "
                           "I can calculate the speed distance/time * 60, but I do not know which date is today.")
            ),
            (
                CheckInputDataInput(
                    instruction="I have eaten a pizza for 5.99$ at the pizzeria, today. The pizza had about 1200 "
                                "calories. Today is the 12th of October and the tax rate is 0.19",
                    parameter="description: str, cal_amount: float, price_net: float, price_gross: float, date: "
                              "datetime.datetime"
                ),
                CheckInputDataOutput(
                    information_sufficient=True,
                    missing_parameters=None,
                    reason="The instruction mentions a gross price, the calories and the date is given. "
                           "As description pizza from a pizzeria is implicit."
                           " I can calculate the net price from the gross price and the tax rate.")
            ),
            (
                CheckInputDataInput(
                    instruction="I have spend a total of 5.99$ for two coffees at Starbucks on June 21st 2022. "
                                "The tax rate is 0.21.",
                    parameter="description: str, net_expense: float, gross_expense: float, tax_rate: float, "
                              "date: datetime.datetime"
                ),
                CheckInputDataOutput(
                    information_sufficient=True,
                    missing_parameters=None,
                    reason="The instruction mentions the gross and net expense and the tax rate. The description "
                           "and the date is given."
                           " I can calculate the net expense from the gross expense and the tax rate by the "
                           "formula net_expense = gross_expense / (1 + tax_rate).")
            )
        ]
        check_job = job_manager.create_job(
            job_name="check_input_data",
            input_model=CheckInputDataInput,
            output_model=CheckInputDataOutput,
            instruction=INSTRUCTION_CHECK,
            example_pairs=examples,
            **kwargs
        )

        return cls(
            name=name,
            tool=tool,
            job=job,
            check_job=check_job,
            description=description,
            job_manager=job_manager,
            **kwargs)

    def add_metrics(self, metrics: dict):
        self.metrics = {
            "execution_time": self.metrics["execution_time"] + metrics["execution_time"],
            "token_usage": self.metrics["token_usage"] + metrics["token_usage"],
            "model_name": self.metrics["model_name"] or metrics["model_name"],
            "model_config": self.metrics["model_config"] or metrics["model_config"],
            "errors": self.metrics["errors"] + metrics["errors"]
        }

    def run(self, input_data: dict, **kwargs):

        # check input

        check_input_data = {
            "instruction": input_data["instruction"],
            "parameter": self.job.output_model.template_schema
        }
        check, rm = self.job_manager.generate_output(self.check_job, check_input_data)

        self.add_metrics(rm)

        if not check["information_sufficient"]:
            self.to_console("Reason", check["reason"], "yellow")
            self.to_console("Missing parameters", str(check["missing_parameters"]), "red")

            return AgentResponse(
                content=f"Can not execute the task because of missing parameters: {check['missing_parameters']}",
                success=False,
                metrics=self.metrics
            )

        tool_input, rm = self.job_manager.generate_output(self.job, input_data)

        self.add_metrics(rm)

        self.to_console("Input", str(tool_input), "yellow")

        output_data = self.tool(**tool_input)
        self.to_console("Output", str(output_data), "yellow")

        return AgentResponse(content=output_data,  success=True, metrics=self.metrics)

    def to_console(self, tag: str, message: str, color: str = "green"):

        color_prefix = Fore.__dict__[color.upper()]

        if self.verbose > 0:
            print(color_prefix + f"{tag}: {message}{colorama.Style.RESET_ALL}")


class DummyAgent(SingleToolAgent):
    name: str
    description: str
    tool: Callable
    job: JobRecord = None
    check_job: JobRecord = None
    job_manager: JobManager = None
    verbose: int = 0

    @classmethod
    def prepare_job(cls, tool: Callable, **kwargs):
        name = kwargs.get("name", tool.__name__)
        description = kwargs.get("description", parse_docstring(tool.__doc__)["short_description"])

        if "name" in kwargs:
            del kwargs["name"]
        if "description" in kwargs:
            del kwargs["description"]

        return cls(name=name, tool=tool, description=description, **kwargs)

    def run(self, *args, **kwargs):
        result = self.tool(*args, **kwargs)
        return AgentResponse(content=result, success=True)


if __name__ == "__main__":

    from datetime import datetime

    class OutputSchema(BaseModel):
        description: str = Field(description="The description of the expense or what the amount was spend for.")
        net_expense: float
        gross_expense: float
        tax_rate: float
        date: datetime

    def add_expense_to_db(description: str, net_expense: int, gross_expense: int, tax_rate: float, **kwargs) -> str:
        """Add an expense to the database."""
        return f"Adding expense to database: {description}, {net_expense}, {gross_expense}, {tax_rate}"

    agent = SingleToolAgent.prepare_job(add_expense_to_db, OutputSchema, verbose=True)

    agent.run({"instruction": "I have spend a total of 5.99$ for two coffees at Starbucks, today. The tax rate is 0.21. Today is the 12th of October 2022."})


