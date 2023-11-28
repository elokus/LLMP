import uuid
from uuid import UUID

from typing import Sequence

def is_valid_uuid(val):
    """
    Check if val is a valid UUID.

    Args:
        val (str): The value to check.
    Returns:
        bool: True if val is a valid UUID, False otherwise.

    Examples:
    >>> is_valid_uuid('c9bf9e57-1685-4c89-bafb-ff5af830be8a')
    True
    >>> is_valid_uuid('c9bf9e58')
    False
    >>> is_valid_uuid('55bcb28633c84af1a9f9caaec204b020')
    True
    """

    try:
        uuid.UUID(str(val))
        return True
    except ValueError:
        return False


def safe_job_name(planned_name: str, existing_names: list, prefix: str = "_v") -> str:
    blocked_names = [name for name in existing_names if name.startswith(planned_name)]
    for name in blocked_names:
        if name.startswith(planned_name):
            return f"{planned_name}{prefix}{len(blocked_names)}"
    return planned_name






if __name__ == '__main__':
    import doctest
    doctest.testmod()
