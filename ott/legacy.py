import pandas as pd
import numpy as np

from .common import loadmat_validate, datenum2datetime
from .common import CLASS2USE, UNCLASSIFIED
from .ml_analyzed import ML_ANALYZED
from .class_scores import TIMESTAMPS, CLASSES, COUNTS, THRESHOLDS, LIDS

FILELIST = 'filelistTB'
MDATE = 'mdateTB'
ML_ANALYZED_TB = 'ml_analyzedTB'

def validate_thresh(thresh):
    if thresh in [None, 'adhoc', 'opt']:
        return
    raise ValueError('unrecognized threshold type {}'.format(thresh))

class MatClassSummary(object):
    """reads a class summary .mat file"""
    def __init__(self, mat_path):
        self.mat = loadmat_validate(mat_path, MDATE, ML_ANALYZED_TB, CLASS2USE)
    def get_timestamps(self):
        """convert matlab timestamps to datetime64s"""
        ts = pd.Series([pd.to_datetime(datenum2datetime(t)) for t in self.mat[MDATE]])
        # now round to the nearest second to deal with MATLAB precision issue
        # as described in http://stackoverflow.com/questions/13785932/how-to-round-a-pandas-datetimeindex
        ts = np.round(ts.astype(np.int64),-9).astype('datetime64[ns]')
        return ts
    def get_thresholds(self, thresh=None):
        """param thresh = None, 'adhoc', or 'opt'"""
        validate_thresh(thresh)
        classes = self.get_classes()
        if thresh == 'adhoc':
            aht = list(self.mat['adhocthresh'])
            return { THRESHOLDS: dict(zip(classes, aht)) }
        else:
            # unable to determine thresholds
            return { }
    def get_classes(self):
        return list(self.mat[CLASS2USE])
    def get_counts(self, thresh=None):
        """param thresh is None, 'adhoc', or 'opt'"""
        validate_thresh(thresh)
        ccv = 'classcountTB'
        if thresh is not None:
            ccv += '_above_{}thresh'.format(thresh)
        data = self.mat[ccv]
        cols = self.get_classes()
        df = pd.DataFrame(data, columns=cols)
        return { c: df[c].tolist() for c in cols }
    def get_ml_analyzed(self):
        return list(self.mat[ML_ANALYZED_TB])
    def to_json(self, thresh=None):
        """return a json-serializable structure compatible
        with what is used by ClassSummary. thresh = None, 'adhoc', or 'opt'"""
        classes = self.get_classes()
        lids = list(self.mat[FILELIST])
        timestamps = [ '{}'.format(ts) for ts in self.get_timestamps() ]
        counts = self.get_counts(thresh)
        ml_analyzed = self.get_ml_analyzed()

        out = {
            CLASSES: classes,
            LIDS: lids,
            TIMESTAMPS: timestamps,
            COUNTS: counts,
            ML_ANALYZED: ml_analyzed
        }
        out.update(self.get_thresholds(thresh))

        return out