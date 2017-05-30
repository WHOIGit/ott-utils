import pandas as pd
import numpy as np
import json

from .common import loadmat_validate, datenum2datetime, unparse_timestamps
from .common import CLASS2USE, UNCLASSIFIED
from .ml_analyzed import ML_ANALYZED, LOOK_TIME, RUN_TIME
from .class_scores import TIMESTAMPS, CLASSES, COUNTS, THRESHOLDS, LIDS
from .class_summary import ClassSummary

FILELIST = 'filelistTB'
MDATE = 'mdateTB'
ML_ANALYZED_TB = 'ml_analyzedTB'

# the following are legacy keys for mat ml_analyzed files
FILELIST_ALL = 'filelist_all'
# these don't have the underbar that the new keys have
RUNTIME = 'runtime'
LOOKTIME = 'looktime'

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
        if thresh == 'adhoc':
            return list(self.mat['adhocthresh'])
        else:
            # unable to determine thresholds
            return None
    def _get_thresholds_dict(self, thresh=None):
        t = self.get_thresholds(thresh)
        if t is None:
            return { }
        else:
            classes = self.get_classes()
            return { THRESHOLDS: dict(zip(classes, t)) }
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
    def to_json(self, thresh=None, file=None):
        """return a json-serializable structure compatible
        with what is used by ClassSummary. thresh = None, 'adhoc', or 'opt'"""
        classes = self.get_classes()
        lids = list(self.mat[FILELIST])
        timestamps = unparse_timestamps(self.get_timestamps())
        counts = self.get_counts(thresh)
        ml_analyzed = self.get_ml_analyzed()

        out = {
            CLASSES: classes,
            LIDS: lids,
            TIMESTAMPS: timestamps,
            COUNTS: counts,
            ML_ANALYZED: ml_analyzed
        }
        out.update(self._get_thresholds_dict(thresh))

        if file is not None:
            json.dump(out, file)
        else:
            return out
    def to_class_summary(self, thresh=None):
        # FIXME this is inefficient because of parsing of timestamps
        return ClassSummary(json_data=self.to_json(thresh=thresh))

class MatMlAnalyzed(object):
    def __init__(self, mat_path):
        self._df = self._read_mat(mat_path)
    def _read_mat(self, path):
        # read a legacy ml_analyzed mat file
        # ignore variables other than the following
        cols = [FILELIST_ALL, LOOKTIME, ML_ANALYZED, RUNTIME]
        mat = loadmat_validate(path, *cols)
        # convert to dataframe
        df = pd.DataFrame({ c: mat[c] for c in cols }, columns=cols)
        df.index = df.pop(FILELIST_ALL) # index by bin LID
        return df
    def to_json(self, file=None):
        j = {
            LIDS: list(self._df.index),
            ML_ANALYZED: list(self._df[ML_ANALYZED]),
            LOOK_TIME: list(self._df[LOOKTIME]),
            RUN_TIME: list(self._df[RUNTIME])
        }
        if file is not None:
            json.dump(j, file)
        else:
            return j