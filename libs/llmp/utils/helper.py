from datetime import datetime
import copy


def safe_getter(key: str, *args, default=None):
    """
    performs get operatation in descending order and returns the first value found

    Args:
        key (str): key to get
        *args: list of dictionaries
        default (Any, optional): default value to return if key not found. Defaults to None.
    """
    def _safe_getter(d: dict):
        return getattr(d, key, None)

    for d in args:
        if hasattr(d, "__getattr__"):
            v = _safe_getter(d)
            if v is not None:
                return v
    return default


def update_by_kwargs(d: dict, **kwargs):
    """Update a dictionary with kwargs."""
    d.update({k: v for k, v in kwargs.items()})
    return d


def get_timestamp():
    """Return a timestamp."""
    return datetime.now().strftime("%Y%m%d%H%M%S")


def flatten(ar: list | tuple) -> list:
    ls = []
    for item in ar:
        if isinstance(item, list) or isinstance(item, tuple):
            ls.extend(flatten(item))
        else:
            ls.append(item)
    return ls


def int_or_float(val):
    if "." in val:
        return float(val)

    return int(val)


class dotdict(dict):
    def __getattr__(self, key):
        if key.startswith('__') and key.endswith('__'):
            return super().__getattr__(key)
        try:
            return self[key]
        except KeyError:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{key}'")

    def __setattr__(self, key, value):
        if key.startswith('__') and key.endswith('__'):
            super().__setattr__(key, value)
        else:
            self[key] = value

    def __delattr__(self, key):
        if key.startswith('__') and key.endswith('__'):
            super().__delattr__(key)
        else:
            del self[key]

    def __deepcopy__(self, memo):
        # Use the default dict copying method to avoid infinite recursion.
        return dotdict(copy.deepcopy(dict(self), memo))