INSTRUCTION_TEMPLATE = """# Instruction
You are reverse engineering a prompt instruction.

Consider the following list of input and output pairs. Based on the input and output pairs reverse engineer the instruction of the task.
Return a yaml formatted list of {num_instructions} instruction strings (Instructions: [...]). 
Each instruction should capture the essence of the task while trying different best practices for writing prompt instructions.
Do not include the details of the input into your instructions. 
It should be a generalized instruction that can be applied to any input in the same format and logic.
All 'Input_output_pairs' are for the same task so each instruction should be generalized to fit for each each input.

[Example]
Number of instructions: 4
Input_output_pairs:
  - Input:
        Object: Apple
        Color: Red
    Output:
        Result: True
  - Input:
        Object: Banana
        Color: Red
    Output:
        Result: False
        Reason: A Banana is not red.
Instructions:
   - You are a specialized fact checker. Your job is to verify if the attribute assigned to an object is correct in the given context. If the attribute is not correct provide a reason for your result. Use the keys 'Result' and (Optional: 'Reason') to return your result.
   - Verify if the color of the object is correct in context of common sense and general knowledge. If the color is correct return 'Result: True'. If the color is incorrect return 'Result: False' and provide a reason for the incorrectness.
   - You are a fact checker that is specialized in verifying the color of fruit objects. If the color of the object is correct return 'Result: True'. If the color is incorrect return 'Result: False' and provide a reason for the incorrectness.
   - You are a color expert. Your job is to verify if the color of the object is correct in context of common sense and general knowledge. You will provided with an Object and a Color and you have to verify if the color of the object is correct. If the color is correct return 'Result: True'. If the color is incorrect return 'Result: False' and provide a reason for the incorrectness.
[Example end]

# Input
Number of instructions: {num_instructions}
Input_output_pairs: {example_set}
---
Instructions: <list, rule=(length={num_instructions})>
"""

INSTRUCTION_ALTERING_TEMPLATE_1 = (
    "Revise the following instruction to enhance clarity and conciseness. "
    "Focus on simplifying complex phrases, eliminating redundant words, and making the "
    "instruction straightforward without losing its original purpose and technical "
    "accuracy."
)

INSTRUCTION_ALTERING_TEMPLATE_2 = (
    "Expand the following instruction by adding necessary context and background "
    "information. Ensure that the added information is directly relevant to the "
    "instruction and aids in understanding the task better, "
    "especially for users who might be new to this topic."
)

INSTRUCTION_ALTERING_TEMPLATE_3 = (
    "Rewrite the following instruction using user-friendly language. "
    "Replace technical terms with simpler, everyday language where possible, "
    "while maintaining the instruction's accuracy and technical integrity. "
    "The revised instruction should be easily understandable by a non-expert audience."
)

INSTRUCTION_ALTERING_TEMPLATE_4 = (
    "Modify the following instruction to include personalized elements. "
    "This can include addressing the user directly, using relatable examples, "
    "or tying the instruction to common user experiences. Ensure the personalization "
    "adds value and does not detract from the clarity of the instruction."
)

INSTRUCTION_ALTERING_TEMPLATE_5 = (
    "Transform the following instruction by incorporating a role assignment. "
    "Choose a role that is relevant and adds an interesting perspective "
    "to the instruction. The role could be a professional "
    "(like a scientist or a journalist), a fictional character, "
    "or any persona that would give a unique twist to the instruction. "
    "Ensure that the role chosen enhances the purpose of the instruction and adds a "
    "distinct style or approach to how the task should be carried out."
)

