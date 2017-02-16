from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from scipy.io import loadmat

# util for converting MATLAB datenum to Python datetime
# as described in http://stackoverflow.com/questions/13965740/converting-matlabs-datenum-format-to-python
def datenum2datetime(matlab_datenum):
    dt = datetime.fromordinal(int(matlab_datenum)) + timedelta(days=matlab_datenum%1) - timedelta(days = 366)
    return dt

def add_spatiotemporal_columns(df, lat=0., lon=0., depth=0.):
    df['latitude'] = lat
    df['longitude'] = lon
    df['depth'] = depth
    return df

class ClassSummary(object):
    def __init__(self, pathname):
        self.mat = loadmat(pathname, squeeze_me=True)
        self.times = self.get_time_index()
    def get_time_index(self):
        ts = pd.Series([pd.to_datetime(datenum2datetime(t)) for t in self.mat['mdateTB']])
        # now round to the nearest second to deal with MATLAB precision issue
        # as described in http://stackoverflow.com/questions/13785932/how-to-round-a-pandas-datetimeindex
        ts = np.round(ts.astype(np.int64),-9).astype('datetime64[ns]')
        return ts
    def ml_analyzed(self, frequency=None):
        """:param frequency: binning frequency (e.g., '1d')"""
        ml_analyzed = self.mat['ml_analyzedTB']
        s = pd.Series(ml_analyzed, index=self.times)
        if frequency is not None:
            s = s.resample(frequency, how='sum')
        return s
    def counts(self, frequency=None, threshold=None):
        """:param frequency: binning frequency (e.g., '1d')
        :param threshold: None, 'adhoc', or 'opt'"""
        class_cols = self.mat['class2useTB']
        key = 'classcountTB'
        if threshold is not None:
            assert threshold in ['adhoc', 'opt'], 'threshold must be "opt" or "adhoc"'
            key = '{}_above_{}thresh'.format(key, threshold)
        class_counts = self.mat[key]
        df = pd.DataFrame(class_counts, columns=class_cols, index=self.times)
        if frequency is not None:
            df = df.resample(frequency, how='sum')
        return df
    def concentrations(self, frequency=None, threshold=None):
        """:param frequency: binning frequency (e.g., '1d')"""
        cc = self.counts(frequency, threshold)
        ml_analyzed = self.ml_analyzed(frequency)
        # divide counts by ml_analyzed
        return cc.div(ml_analyzed, axis=0)
