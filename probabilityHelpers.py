import random


def get_best_index(x, top):
    ordered = sorted(x, reverse=True)
    indeces = sorted(range(len(x)), key=lambda k: x[k], reverse=True)

    unused_probs = 0.0
    for i in range(top, len(ordered)):
        unused_probs += ordered[i]
    for i in range(0, top):
        ordered[i] += unused_probs / top

    prev_limit = 0
    r = random.random()
    for i in range(0, top - 1):
        if prev_limit <= r < prev_limit + ordered[i]:
            return indeces[i]
        prev_limit += ordered[i]

    return indeces[top - 1]

