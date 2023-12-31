from structgenie.base import BaseIOModel
from structgenie.utils.operator.default_loops import parse_default_in_loop, has_defaults, has_loop
from structgenie.utils.parsing import is_none


def parse_default(output_: dict, output_model_: BaseIOModel, **kwargs):
    """Parse default values to output

    Args:
        output_ (dict): Output dict
        output_model_ (OutputModel): OutputModel object
        **kwargs: placeholder, value pairs to replace in default and keys
    """

    val_dict = output_model_.as_dict

    if not has_defaults(val_dict):
        return output_

    for key in val_dict.keys():
        if "." in key or "_info" in key or not has_defaults(output_model_.get_nested_dict(key)):
            continue

        if has_loop(output_model_, key):
            output_[key] = parse_default_in_loop(output_, output_model_, key, **kwargs)[key]

        elif output_model_.get(key).type == "dict":
            output_[key] = parse_default_in_dict(output_.get(key, {}), output_model_, key, **kwargs)

        elif output_model_.get(key).type == "list":
            output_[key] = parse_default_in_list(output_.get(key, []), output_model_, key, **kwargs)

        else:
            output_[key] = output_.get(key) or output_model_.get_default(key, **kwargs)

    return output_


def parse_default_in_dict(output: dict, output_model: BaseIOModel, parent_key: str, **kwargs):
    """Parse default values to nested dict items in loop
    """
    if not has_defaults(output_model.get_nested_dict(parent_key)):
        return output

    val_dict = output_model.get_nested_dict(parent_key, full_key=False)

    for key in val_dict.keys():
        next_parent_key = f"{parent_key}.{key}"
        if "." in key or key == "_info" or not has_defaults(output_model.get_nested_dict(next_parent_key)):
            continue

        default_value = output_model.get_default(next_parent_key, **kwargs)
        if default_value is not None:
            output[key] = output.get(key) if not is_none(output.get(key)) else default_value
        if _is_nested(output_model, next_parent_key):
            if output_model.get(next_parent_key).type == "dict":
                output[key] = parse_default_in_dict(output.get(key, {}), output_model, next_parent_key, **kwargs)
            else:
                output[key] = parse_default_in_list(output.get(key, []), output_model, next_parent_key, **kwargs)
    return output


def parse_default_in_list(output: list, output_model: BaseIOModel, parent_key: str, **kwargs):
    """Parse default values to nested list items"""
    if not has_defaults(output_model.get_nested_dict(parent_key)):
        return output

    default_value = output_model.get_default(parent_key, **kwargs)
    if default_value is not None and is_none(output):
        return default_value

    if _is_nested(output_model, parent_key):
        parsed_list = [parse_default_in_dict(item, output_model, parent_key, **kwargs) for item in output if
                       isinstance(item, dict)]
        return parsed_list
    return output


def _is_nested(output_model: BaseIOModel, key: str) -> bool:
    """Check if key is nested"""
    if len(output_model.get_nested_dict(key)) > 1:
        return True
    return False
