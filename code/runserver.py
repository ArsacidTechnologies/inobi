#!/usr/bin/env python
import sys
from inobi import run
from decouple import config
import subprocess

if __name__ == '__main__':
    subprocess.call(['sh', './init.sh'])
    hooks = False
    if '--with-hooks' in sys.argv:
        hooks = True
    run(host=config('HOST', cast=str, default='0.0.0.0'),
        port=config('PORT', cast=int),
        debug=config('DEBUG', cast=bool, default=False),
        hooks=hooks)


