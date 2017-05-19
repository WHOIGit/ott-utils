import numpy as np
import pandas as pd

from .common import loadmat_validate, datenum2datetime
from .common import CLASS2USE

MDATE = 'mdateTB'
ML_ANALYZED = 'ml_analyzedTB'

def add_spatiotemporal_columns(df, lat=0., lon=0., depth=0.):
    df['latitude'] = lat
    df['longitude'] = lon
    df['depth'] = depth
    return df

class ClassSummary(object):
    """Represents, and performs calculations on, a class summary .mat file"""
    def __init__(self, pathname):
        self.mat = loadmat_validate(pathname, MDATE, ML_ANALYZED, CLASS2USE)
        self.times = self.get_time_index()
    def get_time_index(self):
        """convert matlab timestamps to datetime64s"""
        ts = pd.Series([pd.to_datetime(datenum2datetime(t)) for t in self.mat[MDATE]])
        # now round to the nearest second to deal with MATLAB precision issue
        # as described in http://stackoverflow.com/questions/13785932/how-to-round-a-pandas-datetimeindex
        ts = np.round(ts.astype(np.int64),-9).astype('datetime64[ns]')
        return ts
    def ml_analyzed(self, frequency=None):
        """get the ml_analyzed time series, optionally binning it
        :param frequency: binning frequency (e.g., '1d')"""
        ml_analyzed = self.mat[ML_ANALYZED]
        s = pd.Series(ml_analyzed, index=self.times)
        if frequency is not None:
            s = s.resample(frequency).sum().dropna()
        return s
    def counts(self, frequency=None, threshold=None):
        """get per-class counts, optionally binning and performing thresholding
        :param frequency: binning frequency (e.g., '1d')
        :param threshold: None, 'adhoc', or 'opt'"""
        class_cols = self.mat[CLASS2USE]
        key = 'classcountTB'
        if threshold is not None:
            if threshold not in ['adhoc', 'opt']:
                raise KeyError('threshold must be "opt" or "adhoc"')
            key = '{}_above_{}thresh'.format(key, threshold)
        class_counts = self.mat[key]
        df = pd.DataFrame(class_counts, columns=class_cols, index=self.times)
        if frequency is not None:
            df = df.resample(frequency).sum().dropna()
        return df
    def concentrations(self, frequency=None, threshold=None):
        """get per-class concentrations, optionally binning and performing thresholding
        :param frequency: binning frequency (e.g., '1d')"""
        cc = self.counts(frequency, threshold)
        ml_analyzed = self.ml_analyzed(frequency)
        # divide counts by ml_analyzed
        return cc.div(ml_analyzed, axis=0)
