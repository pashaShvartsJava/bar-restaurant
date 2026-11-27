


class InsufficientStockError(Exception):
    def __init__(self, unavailable_dishes: list):
        self.unavailable_dishes = unavailable_dishes