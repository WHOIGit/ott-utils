from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from scipy.io import loadmat

# util for converting MATLAB datenum to Python datetime
# as described in http://stackoverflow.com/questions/13965740/converting-matlabs-datenum-format-to-python
def datenum2datetime(matlab_datenum):
    dt = datetime.fromordinal(int(matlab_datenum)) + timedelta(days=matlab_datenum%1) - timedelta(days = 366)
    return dt

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
    @property
    def ml_analyzed(self):
        ml_analyzed = self.mat['ml_analyzedTB']
        return pd.Series(ml_analyzed, index=self.times)
    @property
    def counts(self, threshold=None):
        """:param threshold: None, 'adhoc', or 'opt'"""
        class_cols = self.mat['class2useTB']
        key = 'classcountTB'
        if threshold is not None:
            assert threshold in ['adhoc', 'opt'], 'threshold must be "opt" or "adhoc"'
            key = '{}_above_{}thresh'.format(key, threshold)
        class_counts = self.mat[key]
        return pd.DataFrame(class_counts, columns=class_cols, index=self.times)
    @property
    def concentrations(self):
        cc = self.counts
        ml_analyzed = self.ml_analyzed
        # divide counts by ml_analyzed
        return cc.div(ml_analyzed, axis=0)
