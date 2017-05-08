import unittest

import numpy as np

from ifcb.data.adc import SCHEMA_VERSION_1, SCHEMA_VERSION_2

from ..ml_analyzed import compute_ml_analyzed

class MockBinS2():
	def __init__(self):
		self.schema = SCHEMA_VERSION_2
		self.headers = {
			'runTime': 56.8045,
			'inhibitTime': 36.7328 
		}
		self.expected_ml_analyzed = 0.083631917

class TestMlAnalyzed(unittest.TestCase):
	def test_compute_s2(self):
		abin = MockBinS2()
		ml_analyzed, _, _ = compute_ml_analyzed(abin)
		assert np.allclose(ml_analyzed, abin.expected_ml_analyzed)