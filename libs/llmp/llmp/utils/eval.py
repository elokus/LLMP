import copy
import re
import string
from collections import Counter, defaultdict
from typing import Optional, Union



def normalize(s: str) -> str:
    """Lower text and remove punctuation, articles and extra whitespace."""
    s = s.lower()
    exclude = set(string.punctuation)
    s = "".join(char for char in s if char not in exclude)
    s = re.sub(r"\b(a|an|the)\b", " ", s)
    s = " ".join(s.split())
    return s


def get_consensus(answers):
    counts = defaultdict(int)
    for answer in answers:
        counts[answer] += 1
    counts[None] = 0
    return max(counts, key=counts.get)


def fuzzy_match(s1: str, s2: str) -> bool:
    s1 = normalize(s1)
    s2 = normalize(s2)

    if s1 == "" or s2 == "":
        return s1 == s2

    return s1 in s2 or s2 in s1


def f1_score(prediction: str, answers: list[str]) -> float:
    def _f1_score(prediction: str, ground_truth: str):
        prediction_tokens = normalize(prediction).split()
        ground_truth_tokens = normalize(ground_truth).split()
        common = Counter(prediction_tokens) & Counter(ground_truth_tokens)
        num_same = sum(common.values())
        if num_same == 0:
            return 0
        precision = 1.0 * num_same / len(prediction_tokens)
        recall = 1.0 * num_same / len(ground_truth_tokens)
        f1 = (2 * precision * recall) / (precision + recall)
        return f1

    return max([_f1_score(prediction, answer) for answer in answers])
