EXTEND_INPUTS_TEMPLATE = """# Instruction
You are a highly specialized Prompt Engineer. Your job is to create example inputs for a given prompt.
Below you find the instruction of the final prompt and a list of existing example inputs. Extend the list of example inputs by {num_examples} items.
Do not repeat existing example inputs in your response.

# Examples

Instruction: Specify the source data that needs to be collected for the creation of the output based on the description of the output product and the outlined structure of the product.
Number of items: 2
Existing Example Inputs:
  - Description: A marketing report analyzing customer segmentation to be created
    Structure: Introduction, Methodology, Segmentation Results, Analysis, Conclusion
  - Description: A documentation for a local Python project to be created
    Structure: Introduction, Installation, Usage, Examples, Conclusion
---
Outputs:
- Description: A machine learning model for sentiment analysis to be created and trained
  Structure: Data Collection, Preprocessing, Model Training, Evaluation, Deployment
- Description: An action plan to schedule and invite the sales staff to a meeting to be executed
  Structure: Meeting Agenda, Participant List, Meeting Logistics, Follow-up Plan

# Input
Instruction: {instruction}
Number of items: {num_examples}
Existing Example Inputs: {input_example}
# Output
Outputs: <list, rule=(length={num_examples})>
"""

MAJORITY_GRADE_TEMPLATE = """# Instruction
You are comparing different outputs for a given generation task. You are asked to grade the outputs based on their quality from 1 (worst) to 5 (best).
Below you find the instruction and the input for the generation task as well as a list of existing outputs.
Return a list of grades and a step by step reasoning for your grading decision for each output item.
Do not repeat existing outputs in your response instead return the index of the existing output.

  
# Input
Instruction: {instruction}
Input: {input_example}
Outputs: {outputs}
---
Grades: <list, rule=(length={num_outputs})>
Grades.Index: <integer, rule=(min=0, max={num_outputs})>
Grades.Reasoning: <string>
Grades.Grade: <integer, rule=(min=1, max=5)>
"""

COMPARE_AND_SELECT_TEMPLATE = """# Instruction
You are comparing different outputs for a given generation task. You are asked to pick the best output.
Below you find the instruction and the input for the generation task as well as a list of existing outputs.
Select the best option by returning the index of the best output item and a step by step reasoning for your decision.
Do not repeat existing outputs in your response instead return the index of the existing output.
Try to reason your decision as detailed as possible by thinking step by step in context of the task input and explain why you don't select the other options.

# Input
TASK_INSTRUCTION: {task_instruction}
TASK_INPUT: {task_input}
TASK_OUTPUTS: {task_output}
# Output
Result: <dict>
Result.Index: <integer>
Result.Reasoning: <string>
"""

FIND_BEST_TEMPLATE = """# Instruction
You are comparing different outputs for a given generation task. You are asked to pick the best output.
Below you find the instruction and the input for the generation task as well as a list of existing outputs.
Select the best option by returning the index of the best output item and a step by step reasoning for your decision.
The index of the first output item is 0.
Try to reason your decision as detailed as possible by thinking step by step in context of the task input and explain why you don't select the other options.

# Input
TASK_INSTRUCTION: {task_instruction}
TASK_INPUT: {task_input}
TASK_OUTPUTS: {task_output}
# Output
Index: <int>
Reasoning: <multiline>
"""
