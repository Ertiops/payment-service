from collections.abc import Callable

from polyfactory import Use


class IterUse[T](Use):
    def __init__(self, func: Callable[[int], T]) -> None:
        self.count = 0
        self.func = func
        super().__init__(self.next)

    def next(self) -> T:
        self.count += 1
        return self.func(self.count)
