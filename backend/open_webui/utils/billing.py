import math

CREDIT_RATE = 0.0015
def calculate_cost(cost_usd: float) -> int:
    return math.ceil(cost_usd / CREDIT_RATE)
