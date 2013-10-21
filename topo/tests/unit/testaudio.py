# CEBALERT: incomplete!

import unittest
from numpy.testing import assert_array_almost_equal

from topo import pattern
import topo.pattern.audio

from nose.plugins.skip import SkipTest


class TestAudio(unittest.TestCase):

    def setUp(self):
        self.audio = pattern.audio.AudioFile(filename="sounds/complex/daisy.wav")

    def test_basic(self):
        try:
            result = self.audio()
        except:
            raise SkipTest("Daisy not found")

if __name__ == "__main__":
	import nose
	nose.runmodule()