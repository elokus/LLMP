MATCH_RESPONSE = """# Instruction
You are comparing a submitted output to an expert output on a given instruction and input.

Compare the content of the submitted output with the expert output. Ignore any differences in style, grammar, or punctuation.
The submitted output may either be a subset or superset of the expert output, or it may conflict with it. Determine which case applies. Answer the question by selecting one of the following options:
(A) The submitted output is a subset of the expert output and is fully consistent with it.
(B) The submitted output is a superset of the expert output and is fully consistent with it.
(C) The submitted output contains all the same details as the expert output.
(D) There is a disagreement between the submitted output and the expert output.
(E) The outputs differ, but these differences don't matter from the perspective of factuality.

# Input
Instruction: {instruction}
Input: {example_input}
Expert: {ideal_output}
Submission: {output}
---
Reasoning: <str>
Choice: <str, options=[A, B, C, D, E]> 
"""
