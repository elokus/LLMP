from abc import ABC, abstractmethod
from typing import Callable, Type, Optional, Union
import colorama
from colorama import Fore
from openai import OpenAI

from openai.types.chat import ChatCompletionMessageToolCall, ChatCompletionMessage

from llmp.pydantic_v1 import BaseModel, Field
from llmp_agent.base_tool import BaseTool, ToolResult, report_tool


class StepResult(BaseModel):
    event: str
    content: str
    success: bool


class BaseAgent(BaseModel, ABC):
    name: str
    tools: list[BaseTool]

    @abstractmethod
    def run(self, *args, **kwargs):
        pass

    def to_console(self, tag: str, message: str, color: str = "green"):

        color_prefix = Fore.__dict__[color.upper()]

        if self.verbose > 0:
            print(color_prefix + f"{tag}: {message}{colorama.Style.RESET_ALL}")


SYSTEM_MESSAGE = """You are tasked with completing specific objectives and must report the outcomes. At your disposal, you have a variety of tools, each specialized in performing a distinct type of task.

For successful task completion:
Thought: Consider the task at hand and determine which tool is best suited based on its capabilities and the nature of the work.

Use the report_tool with an instruction detailing the results of your work.
If you encounter an issue and cannot complete the task:

Use the report_tool to communicate the challenge or reason for the task's incompletion.
You will receive feedback based on the outcomes of each tool's task execution or explanations for any tasks that couldn't be completed. This feedback loop is crucial for addressing and resolving any issues by strategically deploying the available tools.
"""

TOOL_SUCCESS_MESSAGE = ("Your last action succeed. "
                        "If you have completed the task, "
                        "please use the report_tool to submit the final result to the user's question. "
                        "Otherwise use other tools to continue the task.")

TOOL_FAILED_MESSAGE = ("Your last action failed. "
                       "Review the chat history or use other tools to obtain the correct parameters. "
                       "If you need additional information for the task, "
                       "use the report_tool to ask for additional information.")


class OpenAIAgent(BaseAgent):

    name: str = "AgentOrchestor"
    description: str = "Orchestrate the agents to complete a task."
    tools: list[Union[BaseTool, Tool]]

    client: OpenAI = Field(default_factory=OpenAI)
    model_name: str = "gpt-3.5-turbo-0125"
    token_usage: int = 0

    verbose: int = 3
    memory: list[dict] = Field(default_factory=list)
    step_history: list[Union[dict, ChatCompletionMessage]] = Field(default_factory=list)
    max_steps: int = 5

    system_message: str = SYSTEM_MESSAGE
    tool_success_message: Optional[str] = TOOL_SUCCESS_MESSAGE
    tool_failed_message: Optional[str] = TOOL_FAILED_MESSAGE

    class Config:
        arbitrary_types_allowed = True

    def prepare_tools(self):
        tools = [tool.openai_tool_all_optional for tool in self.tools]
        return [*tools, report_tool.openai_tool_all_optional]

    @property
    def tool_dict(self):
        return {tool.name: tool for tool in self.tools}

    def prepare_input(self, step_result: StepResult | None, user_input, **kwargs):
        if step_result is None:
            messages = [
                {"role": "system", "content": self.system_message},
                {"role": "user", "content": user_input}
            ]
            for message in messages:
                self.step_history.append(message)
            tools = self.prepare_tools()
            return messages, tools

        elif step_result.success:
            messages = [m for m in self.step_history]
            if self.tool_success_message:
                messages.append(
                    {"role": "user",
                     "content": self.tool_success_message
                     }
                )
            tools = self.prepare_tools()
            return messages, tools

        else:
            messages = [m for m in self.step_history]

            if self.tool_failed_message:
                messages.append(
                    {"role": "user",
                     "content": self.tool_failed_message
                     }
                )
            tools = self.prepare_tools()
            return messages, tools

    def run(self, user_input: str, **kwargs):
        self.to_console("START", f"User Input: {user_input}")

        self.memory = kwargs.get("memory", [])
        step_result = None
        i = 0

        while i < self.max_steps:
            try:
                messages, tools = self.prepare_input(step_result, user_input)
                step_result = self.run_step(messages, tools, **kwargs)
                if step_result.event == "finish":
                    break
                i += 1
            except Exception as e:
                self.to_console("Error in execution", str(e), "red")
                raise e

        self.to_console("Final Result", step_result.content, "green")

        return step_result.content

    def run_step(self, messages: list[dict], tools,  **kwargs):

        message, tool_calls = self._plan_step(messages, tools)
        self.step_history.append(message)

        if not tool_calls:
            step_result = StepResult(event="Error", content="No tool calls were returned.", success=False)
            self.to_console("Error", str(step_result), "magenta")
            return step_result

        # execute the tool calls
        tool_results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            args = self.parse_arguments(tool_call)

            self.to_console("Tool Call", f"Name: {tool_name}\nArgs: {args}", "magenta")

            if tool_name == "report_tool":
                tool_result = ToolResult(content=args["report"], success=True)

            elif tool_name not in self.tool_dict:
                tool_result = ToolResult(
                    content=f"Unknown tool: {tool_name}. "
                            f"Please select one of the following tools: {list(self.tool_dict.keys())}",
                    success=False
                )

            else:
                tool = self.tool_dict[tool_name]
                tool_result = tool.run(**args)

            self.to_console("Tool Result", str(tool_result), "yellow")
            tool_results.append((tool_call, tool_result))

        # process the tool results
        for tool_call, tool_result in tool_results:
            if tool_result.metrics:
                self.token_usage += tool_result.metrics.get("token_usage", 0)
            tool_call_message = self.tool_call_message(tool_call, tool_result)
            self.step_history.append(tool_call_message)

            if tool_call.function.name == "report_tool":
                step_result = StepResult(event="finish", content=tool_result.content, success=True)
                return step_result

        all_succeed = all(tool_result.success for _, tool_result in tool_results)
        if all_succeed:
            return StepResult(event="intermediate", content="All tools executed successfully.", success=all_succeed)
        else:
            return StepResult(event="error", content="Some tools failed to execute.", success=all_succeed)

    def _plan_step(self, messages, tools):

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            tools=tools
        )
        message = response.choices[0].message
        tool_calls = message.tool_calls
        self.token_usage += response.usage.total_tokens

        return message, tool_calls

    @staticmethod
    def tool_call_message(tool_call: ChatCompletionMessageToolCall, tool_result: ToolResult):
        return {
            "tool_call_id": tool_call.id,
            "role": "tool",
            "name": tool_call.function.name,
            "content": tool_result.content,
        }

    @staticmethod
    def parse_arguments(tool_call: ChatCompletionMessageToolCall):
        import json
        return json.loads(tool_call.function.arguments)

