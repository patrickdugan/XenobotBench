"""Digital-only exact finite-state observational quotient (MOP-01)."""
from collections import deque

def partition(states, observation, transitions, actions):
    """Return state->equivalence class ID for all future action words."""
    states = tuple(sorted(states))
    assert states and all(s in observation for s in states)
    assert all(action in transitions for action in actions)
    assert all(set(transitions[a]) >= set(states) for a in actions)
    assert all(transitions[a][s] in states for a in actions for s in states)
    def canonical(signatures):
        class_for_signature = {}
        return {s: class_for_signature.setdefault(signatures[s], len(class_for_signature))
                for s in states}
    labels = canonical({s: observation[s] for s in states})
    for _ in range(len(states)):
        signatures = {
            s: (labels[s], tuple(labels[transitions[a][s]] for a in actions))
            for s in states
        }
        new_labels = canonical(signatures)
        if new_labels == labels:
            return labels
        labels = new_labels
    raise AssertionError("finite partition refinement failed to stabilize")

def distinguishing_word(left, right, observation, transitions, actions):
    """Shortest word distinguishing the two public observation traces, or None."""
    pending = deque([(left, right, ())])
    seen = set()
    while pending:
        x, y, word = pending.popleft()
        if (x, y) in seen:
            continue
        seen.add((x, y))
        if observation[x] != observation[y]:
            return word
        for a in actions:
            pending.append((transitions[a][x], transitions[a][y], word + (a,)))
    return None

def demonstration():
    states = (0, 1, 2, 3)
    observations = {0: 0, 1: 0, 2: 1, 3: 1}
    transitions = {
        "restore": {0: 0, 1: 0, 2: 2, 3: 2},
        "toggle": {0: 2, 1: 1, 2: 0, 3: 3},
    }
    return states, observations, transitions
