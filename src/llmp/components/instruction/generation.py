from llmp.components.base import BaseInstructionHandler
from llmp.components.instruction.utils import mutate_instruction, generate_instruction_from_models, instruction_from_working_out


class InstructionGenerator(BaseInstructionHandler):

    def run(self):
        """Run the instruction generation process."""

        if len(self.job.example_records) > 0:
            if self.debug:
                print("Running instruction generation from working out.")

            return instruction_from_working_out(
                input_object=self.job.example_records[0].input,
                output_object=self.job.example_records[0].output,
            )
        else:
            if self.debug:
                print("Running instruction generation from scratch.")

            return generate_instruction_from_models(
                input_model=self.job.input_model,
                output_model=self.job.output_model,
            )
