"""进度显示"""
import sys


class ProgressBar:
    def __init__(self, total: int, label: str = "Progress"):
        self.total = total
        self.label = label
        self.done = 0

    def update(self, n: int = 1):
        self.done += n
        self.render()

    def render(self):
        pct = self.done / max(self.total, 1)
        bar_len = 30
        filled = int(bar_len * pct)
        bar = chr(0x2588) * filled + chr(0x2591) * (bar_len - filled)
        msg = f"\r{self.label} |{bar}| {self.done}/{self.total} ({pct*100:.0f}%)"
        sys.stdout.write(msg)
        sys.stdout.flush()
        if self.done >= self.total:
            print()