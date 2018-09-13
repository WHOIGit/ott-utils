import json

import pandas as pd

from .common import parse_timestamps, unparse_timestamps
from .ml_analyzed import ML_ANALYZED
from .class_scores import TIMESTAMPS, CLASSES, COUNTS, THRESHOLDS

def ml_analyzed2series(counts, timestamps=None):
    """requires ml_analyzed to be merged into count summary
    using merge_ml_analyzed"""
    if timestamps is None:
        timestamps = parse_timestamps(counts[TIMESTAMPS])
    return pd.Series(counts[ML_ANALYZED], index=timestamps)

def counts2df(counts, timestamps=None):
    """consumes data structure produced by summarize_counts
    and produces a Pandas dataframe with one column per class,
    indexed by timestamp"""
    if timestamps is None:
        timestamps = parse_timestamps(counts[TIMESTAMPS])
    classes = counts[CLASSES]
    counts = counts[COUNTS]

    return pd.DataFrame(counts, columns=classes, index=timestamps)

def df2counts(df):
    """consumes a DataFrame with class counts and produces a
    json-serializable dict:
    {
        CLASSES: [class1, class2, ...],
        TIMESTAMPS: [ts1, ts2, ...],
        COUNTS: {
            "class1": [c1, c2, c3, ...],
            "class2": [c1, c2, c3, ...]
            ...
        }
    }
    """
    classes = df.columns
    timestamps = unparse_timestamps(df.index)
    counts = {}
    for k in classes:
        counts[k] = list(df[k])
    return {
        CLASSES: classes,
        TIMESTAMPS: timestamps,
        COUNTS: counts
    }

def concentrations(count_summary, frequency=None):
    """requires ml_analyzed merged into counts"""
    ma = ml_analyzed2series(count_summary)
    counts = counts2df(count_summary)
    if frequency is not None:
        ma = ma.resample(frequency).sum().dropna()
        counts = counts.resample(frequency).sum().dropna()
    return counts.div(ma, axis=0)

class ClassSummary(object):
    def __init__(self, file=None, json_data=None):
        """:param file: json class summary file
        produced by summarize_counts"""
        if file is not None:
            with open(file) as fin:
                self.json = json.load(fin)
        elif json_data is not None:
            self.json = json_data
        else:
            raise ValueError('missing data argument')
        self._timestamps = None
    @property
    def thresholds(self):
        assert THRESHOLDS in self.json, 'missing thresholds'
        return self.json[THRESHOLDS]
    @property
    def classes(self):
        assert CLASSES in self.json, 'missing class labels'
        return self.json[CLASSES]
    def timestamps(self):
        if self._timestamps is None:
            self._timestamps = parse_timestamps(self.json[TIMESTAMPS])
        return self._timestamps
    def counts(self, frequency=None):
        counts = counts2df(self.json, timestamps=self.timestamps())
        if frequency is not None:
            counts = counts.resample(frequency).sum().dropna()
        return counts
    def ml_analyzed(self, frequency=None):
        if not ML_ANALYZED in self.json:
            raise ValueError('no ml_analyzed information in summary')
        ma = ml_analyzed2series(self.json, timestamps=self.timestamps()) 
        if frequency is not None:
            ma = ma.resample(frequency).sum().dropna()
        return ma
    def concentrations(self, frequency=None):
        ma = self.ml_analyzed(frequency)
        c = self.counts(frequency)
        return c.div(ma, axis=0)