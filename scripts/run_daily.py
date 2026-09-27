"""日常运行入口（方便 Task Scheduler / cron 调用）

用法：
  python scripts/run_daily.py            # 完整跑+推送
  python scripts/run_daily.py --dry-run  # 只跑不推
  python scripts/run_daily.py --skip-push
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT))

from src.main import run_pipeline

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--skip-push", action="store_true")
    p.add_argument("--verbose", "-v", action="store_true")
    args = p.parse_args()

    run_pipeline(
        config_path=str(ROOT / "config.yaml"),
        dry_run=args.dry_run,
        skip_push=args.skip_push,
        verbose=args.verbose,
    )
