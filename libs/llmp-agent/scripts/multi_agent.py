from typing import Callable, Type, Optional, Union
import colorama
from colorama import Fore

from structgenie.utils.parsing import dump_to_yaml_string
from .agent import SingleToolAgent
from llmp.data_model import JobRecord
from llmp.pydantic_v1 import BaseModel, Field, validator
from llmp.services.job_manager import JobManager


class InputSchema(BaseModel):
    tools: dict
    task: str


class InputSchemaIntermediate(BaseModel):
    task: str
    tool_used: str
    result: str
    tools: dict


class InputSchemaMissingParams(BaseModel):
    failed_instruction: str
    issue: str
    tools: list[str]


class StepResult(BaseModel):
    event: str
    content: str
    success: bool


class StepAction(BaseModel):
    thought: str
    tool: str
    tool_input: Union[str, dict, None]

    @validator("tool_input")
    def validate_tool_input(cls, v):
        if not isinstance(v, str):
            try:
                v = dump_to_yaml_string(v)
            except:
                raise ValueError(f"Tool input must be a string or a dictionary. Got: {v}")
        return v





class ReportAgent(SingleToolAgent):
    name: str = "report_tool"
    description: str = "Report the result of task completion or when issues occurred."
    tool: Callable = None
    job: JobRecord = None
    check_job: JobRecord = None
    job_manager: JobManager = None
    verbose: bool = False


INSTRUCTION = """You are tasked with completing specific objectives and must report the outcomes. At your disposal, you have a variety of tools, each specialized in performing a distinct type of task. To utilize a tool, specify its name and provide detailed instructions for the task it needs to execute. The tool will process your instructions, perform the task, and enable you to report the results.

For successful task completion:

Thought: Consider the task at hand and determine which tool is best suited based on its capabilities and the nature of the work.
Tool: Clearly identify the tool you intend to use by its specific name.
Instruction: Provide a precise and clear instruction tailored to the tool's functionality, ensuring it has all necessary information to execute the task effectively.
If you complete the task:

Use the report_tool with an instruction detailing the results of your work.
If you encounter an issue and cannot complete the task:

Use the report_tool to communicate the challenge or reason for the task's incompletion.
You will receive feedback based on the outcomes of each tool's task execution or explanations for any tasks that couldn't be completed. This feedback loop is crucial for addressing and resolving any issues by strategically deploying the available tools.

Remember to assess which tool is most appropriate for addressing your current challenge by analyzing the task requirements and the tool's specific capabilities
"""


CHECK_INSTRUCTION = """You are in charge of completing tasks using a set of specialized tools. Each tool performs a specific function. Here's how to proceed:

Identify the Task: Understand the task that needs to be done.
Select the Tool: Choose the tool best suited for this task based on its unique capability.
Craft Instructions: Provide the selected tool with clear, detailed instructions for the task.
Upon task completion:

Report the outcome using the report_tool with a summary of the results.
If unable to complete the task:

Use the ReportTool to explain why the task couldn’t be finished.
Your role involves strategizing which tool to use for each task and reporting on task outcomes or challenges faced..
"""

INTERMEDIATE_INSTRUCTION = """After examining the result of your last tool execution and reflecting on our conversation history, you're now at a crucial decision point in our workflow. Your next steps are as follows:

1. Assess the Current Statu*: Look at the provided result and our previous interactions. Determine how much of the task has been accomplished and what remains to be done.

2. Next Steps:
   - If the Task Is Not Yet Complete: 
     - Thought: Consider why a particular tool is now the right choice based on its capabilities and the task's requirements.
     - Tool: Specify the next tool you intend to use.
     - Tool Input: Write a clear and detailed natural language input string for this tool, incorporating all necessary information to carry out the task.

   - If the Task Is Complete use the report tool to finish the task:
     - Thought: ...
     - Tool: report_tool
     - Tool Input: Provide a comprehensive summary of the results, detailing the completion of the task. Emphasize key outcomes, any significant findings, and the overall conclusion in tool input.

Tools are functions that process natural language instructions as inputs to perform specific tasks.
Your careful evaluation and strategic tool selection are vital for the workflow's progression and eventual success. Ensure your actions are aligned with the goal of efficiently reaching task completion."""


MISSING_PARAMS = """You instructed an agent to complete a task, but you did not provide all the necessary information for the agent to complete the task.
You have a set of tools at your disposal, and you can use them to gather the missing information.
Decide if you are able to gather the missing information using the tools provided to you.
If you are not able to gather the missing information, you should report the missing information to the responsible person by using report tool.
If you can find the missing information in your conversation history, without using the tools, you should update the instrution by using update instruction tool.
When updating the instruction, you should provide the whole updated instruction, not just the missing part as tool input.
"""

METRIC_DEFAULT = {
    "execution_time": 0,
    "token_usage": 0,
    "model_name": None,
    "model_config": {},
    "errors": []
}

class AgentOrchestor(BaseModel):

    name: str = "AgentOrchestor"
    description: str = "Orchestrate the agents to complete a task."
    tools: list[SingleToolAgent]
    job: JobRecord
    job_intermediate: JobRecord
    job_missing_params: JobRecord
    check_job: JobRecord = None
    job_manager: JobManager
    verbose: int = 3
    memory: list[dict] = Field(default_factory=list)
    metrics: dict = METRIC_DEFAULT
    step_history: list[StepAction] = Field(default_factory=list)
    max_steps: int = 10


    class Config:
        arbitrary_types_allowed = True

    def prepare_tools_dict(self):
        tool_dict = {tool.name: tool.description for tool in self.tools}
        tool_dict["report_tool"] = "Report the results or Issues of the task."
        return tool_dict

    @property
    def tool_dict(self):
        return {tool.name: tool for tool in self.tools}

    @classmethod
    def prepare_agent(
            cls,
            tools: list[SingleToolAgent],
            job_manager: JobManager = JobManager(),
            input_model: Type[BaseModel] = InputSchema,
            input_model_intermediate: Type[BaseModel] = InputSchemaIntermediate,
            **kwargs
    ):

        instruction = kwargs.get("instruction", INSTRUCTION)

        for key in ["instruction", "name", "description"]:
            if key in kwargs:
                del kwargs[key]

        job = job_manager.create_job(
            job_name="orchester_agent",
            input_model=input_model,
            output_model=StepAction,
            instruction=instruction,
            **kwargs
        )

        job_intermediate = job_manager.create_job(
            job_name="orchester_agent_intermediate",
            input_model=input_model_intermediate,
            output_model=StepAction,
            instruction=INTERMEDIATE_INSTRUCTION,
            **kwargs
        )

        job_missing_params = job_manager.create_job(
            job_name="orchester_agent_missing_params",
            input_model=InputSchemaMissingParams,
            output_model=StepAction,
            instruction=MISSING_PARAMS,
            **kwargs
        )

        return cls(
            tools=tools,
            job=job,
            job_intermediate=job_intermediate,
            job_manager=job_manager,
            job_missing_params=job_missing_params,
            **kwargs)

    def add_metric(self, metrics: dict):
        if metrics:
            self.metrics = {
                "execution_time": self.metrics["execution_time"] + metrics["execution_time"],
                "token_usage": self.metrics["token_usage"] + metrics["token_usage"],
                "model_name": self.metrics["model_name"] or metrics["model_name"],
                "model_config": self.metrics["model_config"] or metrics["model_config"],
                "errors": self.metrics["errors"] + metrics["errors"]
            }

    def prepare_job(self, step_result: StepResult | None, **kwargs):
        if step_result is None:
            input_data = {"tools": self.prepare_tools_dict(), "task": kwargs.get("task")}
            return self.job, input_data

        elif step_result.success:
            input_data = {
                "tool_used": step_result.event,
                "result": step_result.content,
                "tools": self.prepare_tools_dict(),
                "task": kwargs.get("task")
            }
            return self.job_intermediate, input_data

        elif step_result.event == "Error":
            input_data = {
                "tool_used": self.step_history[-1].tool,
                "result": step_result.content,
                "tools": self.prepare_tools_dict(),
                "task": kwargs.get("task")
            }
            return self.job_intermediate, input_data

        else:
            tools = self.prepare_tools_dict()
            tools["update_instruction"] = "Update the instruction for the task."
            input_data = {
                "failed_instruction": self.step_history[-1].tool_input,
                "issue": step_result.content,
                "tools": tools
            }
            return self.job_missing_params, input_data

    def run(self, **kwargs):

        self.memory = kwargs.get("memory", [])
        step_result = None
        i = 0

        while i < self.max_steps:
            try:
                job, input_data = self.prepare_job(step_result, **kwargs)
                step_result = self.run_step(job, input_data, **kwargs)
                if step_result.event == "report_tool":
                    break
                i += 1
            except Exception as e:
                self.to_console("Error in execution", str(e), "red")
                raise e

        self.to_console("Final Result", step_result.content, "green")

        return step_result.content, self.metrics

    def add_memory(self, role: str, content: Union[str, dict, list] = None):
        if isinstance(content, dict) or isinstance(content, list):
            content = dump_to_yaml_string(content)

        self.memory.append({"role": role, "content": content})

    def _plan_step(self, input_data: dict, planner_job: JobRecord, **kwargs) -> StepAction:
        step_plan, rm = self.job_manager.generate_output(
            planner_job, input_data, memory=self.memory, verbose=self.verbose, **kwargs
        )
        self.add_memory("user", input_data)
        self.add_memory("assistant", step_plan)
        self.add_metric(rm)
        self.to_console("Plan", str(step_plan), "yellow")
        return StepAction(**step_plan)

    def run_step(self, planner_job: JobRecord, input_data: dict,  **kwargs):

        step_plan = self._plan_step(input_data, planner_job, **kwargs)
        self.step_history.append(step_plan)

        if step_plan.tool == "update_instruction":
            prev_step_plan = self.step_history[-2]
            prev_step_plan.tool_input = step_plan.tool_input
            step_plan = prev_step_plan
            self.step_history.append(step_plan)

        if step_plan.tool == "report_tool":
            step_result = StepResult(event="report_tool", content=step_plan.tool_input, success=True)
            self.to_console("Final Result", str(step_result), "green")

        elif step_plan.tool in self.tool_dict:
            tool = self.tool_dict[step_plan.tool]
            result = tool.run({"instruction": str(step_plan.tool_input)})
            self.add_metric(result.metrics)
            step_result = StepResult(event=step_plan.tool, content=result.content, success=result.success)
            self.to_console("Tool Result", str(step_result), "yellow")

        else:
            step_result = StepResult(
                event="Error",
                content=f"Unknown tool: {step_plan.tool}. "
                        f"Please select one of the following tools: {list(self.tool_dict.keys())}",
                success=False
            )
            self.to_console("Error", str(step_result), "yellow")

        return step_result


    def to_console(self, tag: str, message: str, color: str = "green"):

        color_prefix = Fore.__dict__[color.upper()]

        if self.verbose > 0:
            print(color_prefix + f"{tag}: {message}{colorama.Style.RESET_ALL}")


