import time


def format_perf(stated_time: float) -> str:
    return f"{(time.perf_counter() - stated_time) * 1000:.2f} ms"
