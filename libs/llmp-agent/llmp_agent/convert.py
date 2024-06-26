"""Methods for creating function specs in the style of OpenAI Functions"""
import inspect
from typing import (
    Callable,
    Dict,
    Literal,
    Tuple,
    Type,
    Union,
    cast,
)

from typing_extensions import TypedDict
from pydantic_v1 import BaseModel
from copy import deepcopy
from typing import Any, List, Optional, Sequence
import re

from structgenie.components.input_output import OutputModel

PYTHON_TO_JSON_TYPES = {
    "str": "string",
    "int": "integer",
    "float": "number",
    "bool": "boolean",
    "list": "array",
    "listdict": "array",
    "liststr": "array",
    "dict": "object",
}


class FunctionDescription(TypedDict):
    """Representation of a callable function to send to an LLM."""

    name: str
    """The name of the function."""
    description: str
    """A description of the function."""
    parameters: dict
    """The parameters of the function."""


class ToolDescription(TypedDict):
    """Representation of a callable function to the OpenAI API."""

    type: Literal["function"]
    function: FunctionDescription


def _rm_titles(kv: dict) -> dict:
    new_kv = {}
    for k, v in kv.items():
        if k == "title":
            continue
        elif isinstance(v, dict):
            new_kv[k] = _rm_titles(v)
        else:
            new_kv[k] = v
    return new_kv


def convert_pydantic_to_openai_function(
    model: Type[BaseModel],
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    rm_titles: bool = True,
) -> FunctionDescription:
    """Converts a Pydantic model to a function description for the OpenAI API."""
    schema = dereference_refs(model.schema())
    schema.pop("definitions", None)
    title = schema.pop("title", "")
    title = "_".join(split_on_capital_case(title)).lower()
    if "tool" not in title:
        title = f"{title}_tool"
    default_description = schema.pop("description", "")
    return {
        "name": name or title,  # type: ignore
        "description": description or default_description,  # type: ignore
        "parameters": _rm_titles(schema) if rm_titles else schema,
    }


def convert_pydantic_to_openai_tool(
    model: Type[BaseModel],
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
) -> ToolDescription:
    """Converts a Pydantic model to a function description for the OpenAI API."""
    function = convert_pydantic_to_openai_function(
        model, name=name, description=description
    )
    return {"type": "function", "function": function}


def _get_python_function_name(function: Callable) -> str:
    """Get the name of a Python function."""
    return function.__name__


def _parse_python_function_docstring(function: Callable) -> Tuple[str, dict]:
    """Parse the function and argument descriptions from the docstring of a function.

    Assumes the function docstring follows Google Python style guide.
    """
    docstring = inspect.getdoc(function)
    if docstring:
        docstring_blocks = docstring.split("\n\n")
        descriptors = []
        args_block = None
        past_descriptors = False
        for block in docstring_blocks:
            if block.startswith("Args:"):
                args_block = block
                break
            elif block.startswith("Returns:") or block.startswith("Example:"):
                # Don't break in case Args come after
                past_descriptors = True
            elif not past_descriptors:
                descriptors.append(block)
            else:
                continue
        description = " ".join(descriptors)
    else:
        description = ""
        args_block = None
    arg_descriptions = {}
    if args_block:
        arg = None
        for line in args_block.split("\n")[1:]:
            if ":" in line:
                arg, desc = line.split(":", maxsplit=1)
                arg_descriptions[arg.strip()] = desc.strip()
            elif arg:
                arg_descriptions[arg.strip()] += " " + line.strip()
    return description, arg_descriptions


def _get_python_function_arguments(function: Callable, arg_descriptions: dict) -> dict:
    """Get JsonSchema describing a Python functions arguments.

    Assumes all function arguments are of primitive types (int, float, str, bool) or
    are subclasses of pydantic.BaseModel.
    """
    properties = {}
    annotations = inspect.getfullargspec(function).annotations
    for arg, arg_type in annotations.items():
        if arg == "return":
            continue
        if isinstance(arg_type, type) and issubclass(arg_type, BaseModel):
            # Mypy error:
            # "type" has no attribute "schema"
            properties[arg] = arg_type.schema()  # type: ignore[attr-defined]
        elif (
            hasattr(arg_type, "__name__")
            and getattr(arg_type, "__name__") in PYTHON_TO_JSON_TYPES
        ):
            properties[arg] = {"type": PYTHON_TO_JSON_TYPES[arg_type.__name__]}
        elif (
            hasattr(arg_type, "__dict__")
            and getattr(arg_type, "__dict__").get("__origin__", None) == Literal
        ):
            properties[arg] = {
                "enum": list(arg_type.__args__),  # type: ignore
                "type": PYTHON_TO_JSON_TYPES[arg_type.__args__[0].__class__.__name__],  # type: ignore
            }
        if arg in arg_descriptions:
            if arg not in properties:
                properties[arg] = {}
            properties[arg]["description"] = arg_descriptions[arg]
    return properties


def _get_python_function_required_args(function: Callable) -> List[str]:
    """Get the required arguments for a Python function."""
    spec = inspect.getfullargspec(function)
    required = spec.args[: -len(spec.defaults)] if spec.defaults else spec.args
    required += [k for k in spec.kwonlyargs if k not in (spec.kwonlydefaults or {})]

    is_class = type(function) is type
    if is_class and required[0] == "self":
        required = required[1:]
    return required


def convert_python_function_to_openai_function(
    function: Callable,
    name: Optional[str] = None,
) -> Dict[str, Any]:
    """Convert a Python function to an OpenAI function-calling API compatible dict.

    Assumes the Python function has type hints and a docstring with a description. If
        the docstring has Google Python style argument descriptions, these will be
        included as well.
    """
    description, arg_descriptions = _parse_python_function_docstring(function)
    return {
        "name": name or _get_python_function_name(function),
        "description": description,
        "parameters": {
            "type": "object",
            "properties": _get_python_function_arguments(function, arg_descriptions),
            "required": _get_python_function_required_args(function),
        },
    }


def convert_to_openai_function(
    function: Union[Dict[str, Any], Type[BaseModel], Callable],
    name: Optional[str] = None,
    description: Optional[str] = None,
) -> Dict[str, Any]:
    """Convert a raw function/class to an OpenAI function.

    Args:
        function: Either a dictionary, a pydantic.BaseModel class, or a Python function.
            If a dictionary is passed in, it is assumed to already be a valid OpenAI
            function.
        name: The name of the function. If not provided, the name will be inferred from
        description : Optional[str] = None,

    Returns:
        A dict version of the passed in function which is compatible with the
            OpenAI function-calling API.
    """

    if isinstance(function, dict):
        return function
    elif isinstance(function, type) and issubclass(function, BaseModel):
        return cast(Dict, convert_pydantic_to_openai_function(function, name=name, description=description))
    elif callable(function):
        return convert_python_function_to_openai_function(function)
    else:
        raise ValueError(
            f"Unsupported function type {type(function)}. Functions must be passed in"
            f" as Dict, pydantic.BaseModel, or Callable."
        )


def convert_to_openai_tool(
    tool: Union[Dict[str, Any], Type[BaseModel], Callable, OutputModel],
    name: Optional[str] = None,
    description: Optional[str] = None
) -> Dict[str, Any]:
    """Convert a raw function/class to an OpenAI tool.

    Args:
        tool: Either a dictionary, a pydantic.BaseModel class, Python function, or
            BaseTool. If a dictionary is passed in, it is assumed to already be a valid
            OpenAI tool or OpenAI function.
        name: The name of the tool. If not provided, the name will be inferred from the
        description : Optional[str] = None,

    Returns:
        A dict version of the passed in tool which is compatible with the
            OpenAI tool-calling API.
    """


    if isinstance(tool, dict) and "type" in tool:
        return tool
    if isinstance(tool, OutputModel):
        function = convert_output_model_to_openai_function(tool, name, description)
    else:
        function = convert_to_openai_function(tool, name=name, description=description)
    return {"type": "function", "function": function}


def convert_output_model_to_openai_function(model, name: str, description: str) -> Dict[str, Any]:
    parameter = output_model_to_parameters_dict(model)

    return {
        "name": name,  # type: ignore
        "description": description or "",  # type: ignore
        "parameters": parameter,
    }


# --- Utils ---

def output_model_to_parameters_dict(model) -> dict:
    main_properties = {}
    nested_properties = {}
    for line in model.lines:
        if "." in line.key:
            properties = nested_properties
        else:
            properties = main_properties

        properties[line.key] = {'type': remove_typing_annotations(line.type)}
        if line.type == 'date' or line.type == 'datetime' or line.type == 'date-time' or "datetime" in line.type:
            properties[line.key]['format'] = 'date-time'
            properties[line.key]['type'] = 'str'

        properties[line.key]['type'] = PYTHON_TO_JSON_TYPES.get(
            properties[line.key]['type'], properties[line.key]['type']
        )
        if properties[line.key]['type'] == "array":
            if "[" in line.type:
                type_ = remove_typing_annotations(line.type.split("[")[1].split("]")[0])
                properties[line.key]['items'] = {'type': PYTHON_TO_JSON_TYPES.get(type_, type_)}

        if line.description:
            properties[line.key]['description'] = line.description

        if line.options:
            properties[line.key]['enum'] = line.options

    if nested_properties:
        main_properties = unpack_nested_properties(main_properties, nested_properties)

    required = [line.key for line in model.lines if line.default is None and "Optional" not in line.type and "." not in line.key]
    parameters = {'type': 'object', 'properties': main_properties, "required": required}
    return parameters


def unpack_nested_properties(properties: dict, nested_properties: dict) -> dict:
    """unpack nested properties up to 2 levels deep"""

    new_properties = {}
    for key, value in nested_properties.items():
        parent_key = key.split(".")[0]
        child_key = key.split(".")[1]

        if "." in child_key:
            raise ValueError("Nested properties should only be 2 levels deep")

        if parent_key not in new_properties:
            new_properties[parent_key] = {"type": "object", "properties": {}}
        new_properties[parent_key]["properties"][child_key] = value

    for key, value in properties.items():
        if key in new_properties:
            if properties[key]["type"] == "object":
                properties[key]["properties"] = properties[key]["properties"]
            elif properties[key]["type"] == "array":
                properties[key]["items"] = new_properties[key]
            else:
                raise ValueError(f"Unexpected type {properties[key]['type']} in nested properties")
    return properties


def remove_typing_annotations(type_str: str) -> str:
    """Remove typing annotations from a type string."""
    new_type_str = str(type_str)
    return (new_type_str
            .replace("typing.", "")
            .replace("Literal", "enum")
            .replace("Optional", "")
            .replace("Union", "")
            .replace("[", "")
            .replace("]", "")
            .replace("(", "")
            .replace(")", "")
            .replace(" ", "")
            .replace("'", "")
            .replace('"', ""))


def _retrieve_ref(path: str, schema: dict) -> dict:
    components = path.split("/")
    if components[0] != "#":
        raise ValueError(
            "ref paths are expected to be URI fragments, meaning they should start "
            "with #."
        )
    out = schema
    for component in components[1:]:
        if component.isdigit():
            out = out[int(component)]
        else:
            out = out[component]
    return deepcopy(out)


def _dereference_refs_helper(
    obj: Any, full_schema: dict, skip_keys: Sequence[str]
) -> Any:
    if isinstance(obj, dict):
        obj_out = {}
        for k, v in obj.items():
            if k in skip_keys:
                obj_out[k] = v
            elif k == "$ref":
                ref = _retrieve_ref(v, full_schema)
                return _dereference_refs_helper(ref, full_schema, skip_keys)
            elif isinstance(v, (list, dict)):
                obj_out[k] = _dereference_refs_helper(v, full_schema, skip_keys)
            else:
                obj_out[k] = v
        return obj_out
    elif isinstance(obj, list):
        return [_dereference_refs_helper(el, full_schema, skip_keys) for el in obj]
    else:
        return obj


def _infer_skip_keys(obj: Any, full_schema: dict) -> List[str]:
    keys = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "$ref":
                ref = _retrieve_ref(v, full_schema)
                keys.append(v.split("/")[1])
                keys += _infer_skip_keys(ref, full_schema)
            elif isinstance(v, (list, dict)):
                keys += _infer_skip_keys(v, full_schema)
    elif isinstance(obj, list):
        for el in obj:
            keys += _infer_skip_keys(el, full_schema)
    return keys


def dereference_refs(
    schema_obj: dict,
    *,
    full_schema: Optional[dict] = None,
    skip_keys: Optional[Sequence[str]] = None,
) -> dict:
    """Try to substitute $refs in JSON Schema."""

    full_schema = full_schema or schema_obj
    skip_keys = (
        skip_keys
        if skip_keys is not None
        else _infer_skip_keys(schema_obj, full_schema)
    )
    return _dereference_refs_helper(schema_obj, full_schema, skip_keys)


def split_on_capital_case(s):
    """Split a string on capital case letters.

    If multiple capital case letters are together, they are considered as one word.
    """
    matches = re.findall(r'[A-Z][a-z]*', s)
    if not matches:
        return [s]
    result = []
    temp = ''
    for match in matches:
        if len(match) == 1:
            temp += match
        else:
            if temp:
                result.append(temp)
                temp = ''
            result.append(match)
    if temp:
        result.append(temp)
    return result