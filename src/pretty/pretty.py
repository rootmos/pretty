import copy
import io
import json
import mimetypes
import os
import shutil
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, TextIO, Tuple

if not mimetypes.inited:
    mimetypes.init()
    mimetypes.add_type("application/x-yaml", ".yaml")
    mimetypes.add_type("application/x-yaml", ".yml")

@dataclass
class Format:
    name: str
    dump: Callable[[Any, TextIO],None]
    load: Callable[[TextIO],Any]
    mime_type: str

    def is_applicable_extenion(self, ext):
        for e in mimetypes.guess_all_extensions(self.mime_type):
            if e == ext:
                return True
        return False

    @property
    def ext(self):
        return mimetypes.guess_extension(self.mime_type)

    def removesuffix(self, path):
        root, ext = os.path.splitext(path)
        for e in mimetypes.guess_all_extensions(self.mime_type):
            if e == ext:
                return root
        return path

    def loads(self, s: str) -> Any:
        with io.StringIO(s) as buf:
            return self.load(buf)

    def dumps(self, x: Any) -> str:
        with io.StringIO() as buf:
            self.dump(x, buf)
            buf.seek(0)
            return buf.getvalue()

formats = []

class NoAvailableFormats(Exception):
    pass

try:
    import ruamel.yaml
    import ruamel.yaml.scalarstring as ruamel_scalarstring

    ruamel_yaml = ruamel.yaml.YAML()
    ruamel_yaml.default_flow_style = False
    ruamel_yaml.indent(mapping=2, sequence=4, offset=2)
    ruamel_yaml.allow_unicode = True

    def ruamel_dump(d, f):
        d0 = copy.deepcopy(d)
        ruamel_scalarstring.walk_tree(d0)
        ruamel_yaml.dump(d0, f)

    ruamel = Format(
        name = "ruamel",
        dump = ruamel_dump,
        load = lambda f: ruamel_yaml.load(f),
        mime_type = "application/x-yaml",
    )
    formats.append(ruamel)
except ImportError:
    ruamel = None

try:
    import yaml
    try:
        from yaml import CDumper as Dumper
        from yaml import CLoader as Loader
    except ImportError:
        from yaml import Dumper, Loader
    pyaml = Format(
        name = "pyyaml",
        dump = lambda d, f: yaml.dump(d, f, sort_keys=False, Dumper=Dumper),
        load = lambda f: yaml.load(f, Loader=Loader),
        mime_type = "application/x-yaml",
    )
    formats.append(pyaml)
except ImportError:
    pyaml = None

def mk_jq():
    exe = shutil.which("jq")
    if exe is None:
        return

    def jq_dump(d, f):
        p = subprocess.Popen([exe, "."], stdin=subprocess.PIPE, stdout=f)
        p.communicate(input=json.dumps(d).encode("UTF-8"))
        if p.returncode != 0:
            raise RuntimeError(f"jq failed: returncode == {p.returncode}")

    jq = Format(
        name = "jq",
        dump = jq_dump,
        load = json.load,
        mime_type = "application/json",
    )
    formats.append(jq)
    return jq
jq = mk_jq()

json = Format(
    name = "json",
    dump = json.dump,
    load = json.load,
    mime_type = "application/json",
)
formats.append(json)

def pick_format(path) -> Format | None:
    ext = os.path.splitext(path)[1]
    (mt, _) = mimetypes.guess_file_type(path)
    if mt is None:
        return
    for fmt in formats:
        if ext in mimetypes.guess_all_extensions(mt):
            return fmt

def default_format():
    return formats[0]

def load(f: TextIO) -> Tuple[Any, Format]:
    for fmt in formats:
        return fmt.load(f), fmt
    raise NoAvailableFormats()

def dump(x: Any, f: TextIO | None = None) -> Format:
    f = f or sys.stdout
    for fmt in formats:
        fmt.dump(x, f)
        return fmt
    raise NoAvailableFormats()

def loads(s: str) -> Tuple[Any, Format]:
    for fmt in formats:
        return fmt.loads(s), fmt
    raise NoAvailableFormats()

def dumps(x: Any) -> Tuple[str, Format]:
    for fmt in formats:
        return fmt.dumps(x), fmt
    raise NoAvailableFormats()

def loads0(s: str) -> Any:
    return loads(s)[0]
def dumps0(x: Any) -> str:
    return dumps(x)[0]
