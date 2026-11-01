"""TEST ONLY: kill this process after one native result is durable, before job commit.

Run in the experiment's Python environment with a partially completed prototype
directory. Expected exit code is 89. Resume using the ordinary CLI afterwards.
No source file is changed and the kernel releases the experiment writer lock.
"""
import os
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import multiobjective_lab as mo
import score_lab as lab

if __name__=='__main__':
    directory=Path(sys.argv[1]).resolve()
    with lab.RunLock(directory):
        log=lab.Invocation(directory)
        try:
            engine=mo.Engine(directory,log,1,100)
            def crash(stage,key):
                if stage=='after_result_publish' and key.startswith('render-'):
                    log.event('TEST_ONLY_injected_process_death',job=key,exitCode=89)
                    os._exit(89)
            engine.fault_hook=crash
            engine.drive()
        finally:log.close()
