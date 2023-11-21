from llmp.components.base import BaseInstructionHandler
from llmp.components.instruction.utils import mutate_instruction, extend_instruction_by_model


class InstructionMutation(BaseInstructionHandler):
    """Generate Mutated Instructions.

    Can only be used if an instruction is already given.
    """

    def run(self, num_samples_per_mutation: int = 2):
        """Run the instruction generation process."""

        mutated_instructions = mutate_instruction(
            instruction=self.job.instruction,
            num=num_samples_per_mutation,
        )

        results = []
        for instruction in mutated_instructions:
            results.append(
                extend_instruction_by_model(
                    instruction=instruction,
                    input_model=self.job.input_model,
                    output_model=self.job.output_model,
                )
            )

        return results
