INSTRUCTION_FROM_MODEL = """I have a task that takes an input and produces an output. Below you will find the input and output models for that task which define and restrict the possible input objects and the desired output object.
I have lost the instruction for that task. Can you help me work out what it was?
Think step-by-step to reverse engineer the task instruction. What other inputs might look like with the mentioned keys? What is the relationship between them? What might be the right operation (label, extract, compress, generate, etc.) to get from any input object with that structure to the desired output object?


# Input
Input Model: {inp_model}
Output Model: {out_model}
---
Reasoning: <str>
Instruction: <str>
"""

INSTRUCTION_FROM_MODEL_AND_EXAMPLES = """Create the task instruction based on the input and output model for the task provided below. The Input and Output Object are provided as a guide to the format of the input and output objects. The input and output objects may be different for each task but will have the same keys. So you should not include any information from the example given, instead you should use the input and output keys to describe the input and output objects.
Think step-by-step to reverse engineer the task instruction. What other inputs might look like with same keys? What is the relationship between them? What might be the right operation (label, extract, compress, generate, etc.) to get from any input with that structure to the output?

Remember do not include concrete values provided in Input Object and Output Object in your instruction. Instead, use the input and output model to describe the input and output objects so that your instruction can be applied to other inputs and outputs with the same model.


# Input
Input Model: {inp_model}
Output Model: {out_model}
Example Input Object: {input_object}
Example Output Output: {output_object}
---
Reasoning: <str>
Instruction: <str>
"""

INSTRUCTION_FROM_WORKING_OUT = """I gave a friend an instruction and some advice. They followed the instruction to get and advice to use the input and got the correct output.
Below are the correct examples of his workings out. Can you work out what the instruction was without mentioning the details of the working out example?

    
# Input
Input: {input_object}
Output: {output_object}
---
The Instruction was: <str>
"""

MUTATE_INSTRUCTION = """# Instruction
{mutation_instruction}

# Input
Instruction: {instruction}
Number of Mutations: {num_mutations}
---
Mutated Instructions: <list, rule=(length={num_mutations})>
"""

EXTEND_MUTATE_INSTRUCTION_BY_MODEL = """# Instruction
We have a task that takes an input and produces an output. We have lost the details and the instruction for that task.
We have managed to reconstruct the following instruction so far: {mutate_instruction}
Now we have also found the input and output model for that task which define and restrict the possible input objects and the desired output object.
From the input and output model below, can you help us to extend the instruction?
Think step-by-step to reconstruct a detailed task instruction. What hints should we add to the instruction?

# Input
Input Model: {inp_model}
Output Model: {out_model}
---
Reasoning: <str>
The Instruction Was: <str>
"""

EXTEND_MUTATE_INSTRUCTION_BY_EXAMPLE = """# Instruction
We have a task that takes an input and produces an output. We have lost the details and the instruction for that task.
We have managed to reconstruct the following instruction so far: {mutate_instruction}
Now we have found an input/output example for that task.
From the input and output example below, can you help us to extend the instruction without mentioning the details of the example?
Think step-by-step to reconstruct a detailed task instruction. What hints should we add to the instruction?
DON'T add details from the Example as the task will have different inputs and outputs.

# Input
Input Example: {input_example}
Output Example: {output_example}
---
Reasoning: <str>
The Instruction Was: <str>
"""