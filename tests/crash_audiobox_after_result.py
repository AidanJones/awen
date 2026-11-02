"""TEST ONLY: real process death after durable local inference publication."""
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import audiobox_lab as probe


def crash(stage, key):
    if stage == 'after_result_publish':
        os._exit(89)


probe.run(Path(sys.argv[1]), max_new=1, fault_hook=crash)
