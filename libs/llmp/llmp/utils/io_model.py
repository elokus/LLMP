from functools import singledispatch

from structgenie.pydantic_v1 import BaseModel
from structgenie.components.input_output import InputModel, OutputModel

from llmp.types import IOModelDefinition, UnionIOModel
import hashlib

# === hash_from_model ===

def hash_from_io_models(input_model: UnionIOModel, output_model: UnionIOModel, instruction: str = None):
    """Create a hash from a model.

    model must be either InputModel or OutputModel.
    """
    input_model = load_input_model(input_model)
    output_model = load_output_model(output_model)

    models = str(input_model) + str(output_model)
    if instruction:
        models += instruction

    return hashlib.md5(bytes(str(models), "utf-8")).hexdigest()


# === InputModel ===

def load_input_model(model: IOModelDefinition):
    if isinstance(model, ModelMetaclass):
        return InputModel.from_pydantic(model)
    return parse_input_model(model)


@singledispatch
def parse_input_model(model):
    raise NotImplementedError("Unsupported type")


@parse_input_model.register
def _(model: str):
    return InputModel.from_string(model)


@parse_input_model.register
def _(model: InputModel):
    return model


@parse_input_model.register
def _(model: dict):
    return InputModel(**model)

# === OutputModel ===


def load_output_model(model: IOModelDefinition):
    if issubclass(model, BaseModel):
        return OutputModel.from_pydantic(model)
    return parse_output_model(model)


@singledispatch
def parse_output_model(model):
    raise NotImplementedError("Unsupported type")


@parse_output_model.register
def _(model: str):
    return OutputModel.from_string(model)


@parse_output_model.register
def _(model: OutputModel):
    return model


@parse_output_model.register
def _(model: dict):
    return OutputModel(**model)
