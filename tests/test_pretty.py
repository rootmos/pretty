import io
import os
import unittest
import tempfile

import pretty

from parameterized import parameterized


class Formats(unittest.TestCase):
    def test_default_format(self):
        fmt = pretty.default_format()

        # TODO depends on dependencies: matrix test with different sets of dependencies?
        assert fmt.mime_type == "application/x-yaml"
        assert fmt.ext == ".yaml"

    def test_pick_format(self):
        assert pretty.pick_format(path="foo.yaml") == pretty.ruamel

roundtrip_test_values = [
    (None),
    (7),
    ("hello?"),
    ({"foo": 7}),
    ({"foo": {"bar": True}}),
    ({"multiline": "hello\nmulti-line\nworld!"}),
]

class RoundTripBuffer(unittest.TestCase):
    @parameterized.expand(roundtrip_test_values)
    def test_roundtrip_default_format_buffer(self, value):
        with io.StringIO() as buf:
            fmt = pretty.dump(value, buf)
            buf.seek(0)
            assert value == fmt.load(buf)

class RoundTripFile(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="pretty")

    def tearDown(self):
        self.tmp.cleanup()

    @parameterized.expand(roundtrip_test_values)
    def test_roundtrip_default_format_file(self, value):
        fmt = pretty.default_format()
        path = os.path.join(self.tmp.name, "foo" + fmt.ext)
        with open(path, "w") as f:
            fmt.dump(value, f)

        with open(path) as f:
            actual = fmt.load(f)

        assert actual == value

class RoundTripString(unittest.TestCase):
    @parameterized.expand(roundtrip_test_values)
    def test_roundtrip(self, value):
        s, fmt = pretty.dumps(value)
        assert value == fmt.loads(s)

    @parameterized.expand(roundtrip_test_values)
    def test_roundtrip_default_format(self, value):
        assert value == pretty.loads0(pretty.dumps0(value))
