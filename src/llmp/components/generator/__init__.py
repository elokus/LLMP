"""Generator module
Used to perform generation tasks for a given job and input object."""

from .simple import Generator
from .concurrent import *
from .consensus import MajorVoteGenerator
from .examples import ExampleGenerator
