"""Utilities for generating instructions for a job.

Mutation prompts and working out prompt where taken from the following paper:
References: Google DeepMinde PromptBreeder: https://arxiv.org/pdf/2309.16797.pdf
"""

from typing import Type
from pydantic import BaseModel

from llmp.data_model import JobRecord
from llmp.integration.structgenie import Engine, InputModel, OutputModel

import llmp.components.instruction._prompts as template


def mutate_instruction(instruction: str, num: int = 2, **kwargs) -> list[str]:
    """Mutate an instruction by randomly changing one character."""
    mutation_instructions = [
        "Say that instruction again in another way. DON’T use any of the words in the original instruction there’s a good chap.",
        "Make a variant of the instruction. Let's think step by step.",
        "Request More Detailed Responses: If the original prompt is ’Describe X,’ the improved version could be, ’Describe X, focusing on its physical features, historical significance, and cultural relevance.’"
        "Include Multiple Perspectives: For a instruction like ’What is the impact of X on Y?’, an improved version could be, ’What is the impact of X on Y from the perspective of A, B, and C?’"
    ]

    mutated_instructions = []

    for mut_inst in mutation_instructions:

        engine = Engine.from_template(
            template.MUTATE_INSTRUCTION,
            prompt_kwargs={"set_format_tags": False},
            **kwargs
        )
        result, metrics = engine.run(
            dict(
                instruction=instruction,
                mutation_instruction=mut_inst,
                num_mutations=num,
            )
        )
        mutated_instructions.extend(result["mutated_instructions"])
    return mutated_instructions


def extend_instruction_by_model(instruction: str, input_model: InputModel, output_model: OutputModel, **kwargs) -> str:
    """Extend an instruction with context of input and output model."""

    engine = Engine.from_template(
        template.EXTEND_MUTATE_INSTRUCTION_BY_MODEL,
        prompt_kwargs={"set_format_tags": False},
        **kwargs
    )

    result, metrics = engine.run(
        dict(
            mutate_instruction=instruction,
            inp_model=input_model.template_schema,
            out_model=output_model.template_schema,
        )
    )
    return result["the_instruction_was"]


def extend_instruction_by_example(instruction: str, input_example: dict, output_example: dict, **kwargs) -> str:
    """Extend an instruction with context of input and output model."""

    engine = Engine.from_template(
        template.EXTEND_MUTATE_INSTRUCTION_BY_EXAMPLE,
        prompt_kwargs={"set_format_tags": False},
        **kwargs
    )

    result, metrics = engine.run(
        dict(
            mutate_instruction=instruction,
            input_example=input_example,
            output_example=output_example,
        )
    )
    return result["the_instruction_was"]

def instruction_from_working_out(input_object: dict, output_object: dict, **kwargs) -> str:
    """Generate an instruction from the working out."""

    engine = Engine.from_template(
        template.INSTRUCTION_FROM_WORKING_OUT,
        prompt_kwargs={"set_format_tags": False},
        **kwargs
    )

    result, metrics = engine.run(
        dict(
            input_object=input_object,
            output_object=output_object,
        )
    )
    return result["the_instruction_was"]


def generate_instruction_from_model_and_template(
        input_model: InputModel,
        output_model: OutputModel,
        input_object: dict = None,
        output_object: dict = None,
        **kwargs):
    """Generate an instruction for a specific job."""

    engine = Engine.from_template(
        template.INSTRUCTION_FROM_MODEL_AND_EXAMPLES,
        prompt_kwargs={"set_format_tags": False},
        **kwargs
    )

    result, metrics = engine.run(
        dict(
            inp_model=input_model.template_schema,
            out_model=output_model.template_schema,
            input_object=input_object,
            output_object=output_object,
        )
    )

    return result["instruction"]


def generate_instruction_from_models(
        input_model: InputModel,
        output_model: OutputModel,
        **kwargs):
    """Generate an instruction for a specific job."""

    engine = Engine.from_template(
        template.INSTRUCTION_FROM_MODEL,
        prompt_kwargs={"set_format_tags": False}, **kwargs)

    result, metrics = engine.run(
        dict(
            inp_model=input_model.template_schema,
            out_model=output_model.template_schema,
        )
    )

    return result["instruction"]