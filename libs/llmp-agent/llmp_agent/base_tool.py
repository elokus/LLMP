from typing import Callable, Type, Optional, List, get_args, Literal
import inspect
from llmp.pydantic_v1 import BaseModel
from structgenie.components.input_output import OutputModel
from structgenie.components.input_output.line import IOLine
from structgenie.components.validation import Validator

from .convert import convert_to_openai_tool, split_on_capital_case


class ToolResult(BaseModel):
    content: str
    success: bool
    metrics: Optional[dict] = None


class BaseTool(BaseModel):
    name: str
    description: Optional[str] = None
    model: OutputModel
    function: Optional[Callable] = None
    validate_input: bool = True

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def from_pydantic(cls, model: Type[BaseModel], function: Callable = None, name: str = None):
        if not name:
            title = split_on_capital_case(model.schema()["title"])
            title = "_".join(title).lower()
            if not "tool" in title:
                title = f"{title}_tool"
        else:
            title = name

        return cls(name=title, model=OutputModel.from_pydantic(model), function=function)

    @classmethod
    def from_function(cls, function: Callable):
        model = create_output_model_from_function(function)
        name = function.__name__
        if not "tool" in name:
            name = f"{name}_tool"
        return cls(name=name, model=model, function=function)

    def run(self, **kwargs) -> ToolResult:
        if self.validate_input:
            validator = Validator.from_output_model(self.model)
            validation_errors = validator.validate(kwargs)
            if validation_errors:
                content = "\n".join([str(v) for v in validation_errors])
                return ToolResult(content=content, success=False)
        try:
            result = self.function(**kwargs)
        except TypeError as e:
            result = self.function(kwargs)
        if isinstance(result, ToolResult):
            return result

        return ToolResult(content=str(result), success=True)

    @property
    def openai_tool(self):
        return convert_to_openai_tool(self.model, name=self.name, description=self.description)

    @property
    def openai_tool_all_optional(self):
        openai_tool = self.openai_tool.copy()
        if openai_tool["function"]["parameters"].get("required"):
            # remove required fields
            del openai_tool["function"]["parameters"]["required"]
        return openai_tool

    @property
    def openai_tool_schema(self):
        return self.openai_tool_all_optional


def create_output_model_from_function(func):
    sig = inspect.signature(func)
    lines = []
    docstring = inspect.getdoc(func)
    descriptions = {}

    if not docstring is None:
        doclines = docstring.split('\n')
        for line in doclines:
            if ': ' in line:
                key, description = line.split(': ', 1)
                if "(" in key:
                    key = key.split("(")[0]
                descriptions[key.strip()] = description.strip()

    for name, param in sig.parameters.items():
        if param.annotation is not param.empty:
            default = param.default if param.default is not param.empty else None
            options = None
            type_ = str(param.annotation)
            if "typing." in str(param.annotation):
                type_ = type_.split(".")[-1]
            if getattr(param.annotation, '__origin__', None) == Literal:
                options = get_args(param.annotation)
                type_ = "string"
            description = descriptions.get(name, None)
            line = IOLine(key=name, type=type_, default=default, options=options, description=description)
            lines.append(line)
    return OutputModel(lines=lines)


report_tool = BaseTool(
    name="report_tool",
    model=OutputModel(lines=[
        IOLine(key="report", type="string", description="The final answer to the user input or issues occurred during the process."),
    ]),
    function=lambda report: f"Final Report: {report}",
    description="This tool is used to report the final answer to the user input or issues occurred during the process.",
    validate_input=False
)

