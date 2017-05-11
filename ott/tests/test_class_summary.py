import unittest
import os

import numpy as np

from ..class_summary import ClassSummary

SUMMARY_FILE = os.path.join('ott','tests','data','summary_allTB2006.mat')

class TestClassSummary(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cs = ClassSummary(SUMMARY_FILE)
    def setUp(self):
        self.cs = TestClassSummary.cs
    def test_time_index(self):
        ts = self.cs.get_time_index()[0]
        assert str(ts) == '2006-06-06 18:13:59'
    def test_ml_analyzed_no_binning(self):
        ma = self.cs.ml_analyzed()
        assert np.allclose(ma[0], 3.7530310125)
    def test_ml_analyzed_binning(self):
        freqs = ['1d','5d']
        vals = [59.6381817646, 1076.20752513]
        for freq, val in zip(freqs, vals):
            ma = self.cs.ml_analyzed(freq)
            assert np.allclose(ma[0], val)
    def test_counts_no_binning(self):
        df = self.cs.counts()
        assert np.allclose(df.head().Chaetoceros, [26,36,37,19,23])
    def test_counts_binning(self):
        df = self.cs.counts('2d')
        assert np.allclose(df.head().Chaetoceros, [2915, 3363, 3769, 3946, 6242])
    def test_counts_opt_no_binning(self):
        df = self.cs.counts(threshold='opt')
        assert np.allclose(df.head().Chaetoceros, [22, 26, 21, 16, 14])
    def test_counts_opt_binning(self):
        df = self.cs.counts(threshold='opt',frequency='2d')
        assert np.allclose(df.head().Chaetoceros, [2034, 2542, 2593, 2596, 4036])
    def test_counts_adhoc_no_binning(self):
        df = self.cs.counts(threshold='adhoc')
        assert np.allclose(df.head().Chaetoceros, [1, 0, 0, 0, 0])
    def test_counts_adhoc_binning(self):
        df = self.cs.counts(threshold='adhoc',frequency='2d')
        assert np.allclose(df.head().Chaetoceros, [19, 9, 14, 38, 56])
    def test_conc_no_binning(self):
        df = self.cs.concentrations()
        assert np.allclose(df.head().Chaetoceros, [6.927734, 9.097246, 9.480991, 4.495636, 5.287275])
    def test_conc_binning(self):
        df = self.cs.concentrations('2d')
        assert np.allclose(df.head().Chaetoceros, [6.716370, 8.089566, 8.254523, 8.248902,14.198627])
    def test_conc_opt_no_binning(self):
        df = self.cs.concentrations(threshold='opt')
        assert np.allclose(df.head().Chaetoceros, [5.8619286456002886, 6.5702330537474536, 5.3811027203396069, 3.7857989511361185, 3.2183414813566076])
    def test_conc_opt_binning(self):
        df = self.cs.concentrations(threshold='opt',frequency='2d')
        assert np.allclose(list(df.head().Chaetoceros), [4.6864826259129329, 6.114682544971159, 5.678953838031302, 5.426799013302479, 9.1806566726160064])
    def test_conc_adhoc_no_binning(self):
        df = self.cs.concentrations(threshold='adhoc')
        assert np.allclose(df.head().Chaetoceros, [0.266451, 0, 0, 0, 0])
    def test_conc_adhoc_binning(self):
        df = self.cs.concentrations(threshold='adhoc',frequency='5d')
        assert np.allclose(df.head().Chaetoceros, [0.027875664590170997, 0.092325469830652512, 0.32892901692545662, 0.017067472128192224, 0.040908043353465297])
