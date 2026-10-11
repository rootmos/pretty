import logging
import os
import shutil
import string
import subprocess
import sys
import tempfile
from typing import Any, Callable, cast

from . import env, pretty, whoami

logger = logging.getLogger(__name__)

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def temporary_directory(what=None):
    return tempfile.TemporaryDirectory(prefix=f"{whoami}-{what + '-' if what else ''}")

def find_editor():
    e = env("EDITOR")
    if e is not None:
        return e

    e = os.environ.get("EDITOR")
    if e is not None:
        return e

    for e in ["nvim", "vim", "vi", "emacs", "nano"]:
        e = shutil.which(e)
        if e is not None:
            return e

    raise RuntimeError("unable to find an editor")

def run_with_tty(*cmdline, check=None):
    if check is None:
        check = True
    logger.debug(f"running with tty: {cmdline}")
    with open("/dev/tty", "rb") as i, open("/dev/tty", "wb") as o:
        p = subprocess.run(cmdline, check=check, stdin=i, stdout=o)
    return p.returncode == 0

def edit[A](x: Any, editor=None, what="edit", satisfactory: Callable[[Any], A | None ] | None = None) -> A:
    editor = editor or find_editor()

    fmt = pretty.default_format()
    with temporary_directory(what=what) as tmp:
        fn = os.path.join(tmp, what + fmt.ext)
        if satisfactory is None:
            with open(fn, "x") as f:
                fmt.dump(x, f)

            if run_with_tty(editor, fn):
                with open(fn, "r") as f:
                    return cast(A, fmt.load(f))
            else:
                raise RuntimeError("don't know how to interactively edit file: %s", fn)
        else:
            while True:
                with open(fn, "w") as f:
                    fmt.dump(x, f)

                try:
                    if run_with_tty(editor, fn):
                        with open(fn, "r") as f:
                            x = fmt.load(f)

                        y = satisfactory(x)
                        if y:
                            return cast(A, y)
                except Exception as e:
                    eprint(f"oops: {e}")
                    input("press the any key... to attempt again")
