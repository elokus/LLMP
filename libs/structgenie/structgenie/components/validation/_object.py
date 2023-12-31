from typing import Union

from structgenie.base import BaseIOModel
from structgenie.components.input_output import build_output_schema


def validation_config_nested(key: str, val_config: dict) -> dict:
    return {k.replace(f"{key}.", ""): v for k, v in val_config.items() if k.startswith(f"{key}.")}


def required_keys(validation_config: dict):
    return [
        key for key in validation_config.keys()
        if
        not validation_config[key].get("type", "").startswith("Optional") and "." not in key and not key.startswith("$")
    ]


def validate_keys(d: dict, val_config: dict) -> Union[str, None]:
    missing_keys = [key for key in required_keys(val_config) if key not in d]
    for key in missing_keys:
        if key in val_config and val_config[key].get("default", None):
            missing_keys.remove(key)
    if missing_keys:
        return f"Keys {missing_keys} not in output"
    return None


def nested_key_validation(key: str, value: any, output_model: BaseIOModel = None, inputs: dict = None):
    errors = []

    if output_model and not key.startswith("$"):
        schema = build_output_schema(output_model, inputs=inputs)
        for i, _k in enumerate(key.split(".")):
            schema = schema[_k]
        if isinstance(schema, list):
            for item_schema in schema:
                errors.extend(_nested_key_validation(value, output_model, item_schema))
        else:
            errors.extend(_nested_key_validation(value, output_model, schema))

    return errors


def _nested_key_validation(value: any, output_model: BaseIOModel = None, schema: dict = None):
    errors = []
    if not isinstance(schema, dict):
        return errors

    for k, v in schema.items():
        if isinstance(value, list) and isinstance(value[0], dict):
            value_ = [v_ for v_ in value if k in v_][0]
        else:
            value_ = value

        if k not in value_:
            errors.append(f"Key '{k}' not in output")
            continue
        if isinstance(v, dict):
            errors.extend(_nested_key_validation(value_[k], output_model, v))
    return errors


def is_nested(key, val_config) -> bool:
    if validation_config_nested(key, val_config):
        return True
    return False
