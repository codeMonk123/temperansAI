from copy import deepcopy


class DecisionCache:
    """
    Small deterministic in-memory routing cache.

    Persistence of trajectories is separate.
    """

    def __init__(self):
        self._items = {}

    def get(self, signature):
        value = self._items.get(signature)

        if value is None:
            return None

        return deepcopy(value)

    def put(self, signature, value):
        self._items[signature] = deepcopy(value)

    def clear(self):
        self._items.clear()

    def __len__(self):
        return len(self._items)
