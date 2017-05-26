import os
from glob import glob
import json 
import pandas as pd
import numpy as np
from scipy.io import loadmat

from ifcb.data.identifiers import Pid

from .common import loadmat_validate, split_column
from .common import CLASS2USE, UNCLASSIFIED

from .ml_analyzed import ML_ANALYZED, ml_analyzed2dict

SCORES = 'TBscores'
CLASSIFIER_NAME = 'classifierName'
OPT_THRESHOLDS = 'maxthre'
CLASSES = 'classes'

THRESHOLDS = 'thresholds'
TIMESTAMPS = 'timestamps'
LIDS = 'lids'
COUNTS = 'counts'

CLASS_GLOB = '*_class_v1.mat'

class ClassScores(object):
    """represents a single class scores file"""
    def __init__(self, path):
        f = loadmat_validate(path, CLASS2USE, SCORES)
        self.class2use = f[CLASS2USE]
        self.class2count = self.class2use[:-1] # exclude "unclassified"
        s = f[SCORES]
        # unsqueeze the TBScores matrix in the one-ROI case
        if(len(s.shape)==1):
            s = np.array([s])
        self.scores = pd.DataFrame(s,columns=self.class2count)
    def class_counts(self, thresh={}):
        """compute per-class counts for this file.
        thresh is dict mapping class name -> threshold"""
        thresh = np.array([[thresh.get(k,0) for k in self.class2count]])
        # zero all cells that are under the corresponding class's threshold
        over_thresh = (self.scores > thresh) * self.scores
        # find max class over threshold
        max_class = over_thresh.idxmax(axis=1)
        # exclude rows where all scores > thresh are zero
        sum_over_thresh = over_thresh.sum(axis=1)
        max_class = max_class[sum_over_thresh > 0]
        # count the number of occurrences of each value
        counts = max_class.value_counts()
        # rows that were excluded are 'unclassified'
        unc_count = len(self.scores) - len(max_class)
        counts[UNCLASSIFIED] = unc_count
        # convert to array indexed by class2use
        class_counts = [counts.get(k,0) for k in self.class2use]
        return class_counts

def find_class_files(class_dir):
    return glob(os.path.join(class_dir, CLASS_GLOB))

def get_opt_thresh(class_dir, classifier_dir):
    try:
        # arbitrarily pick the first one, all should use the same classifier
        class_path = list(find_class_files(class_dir))[0]
    except IndexError:
        raise FileNotFoundError('no class score files found in {}'.format(class_dir))
    classfile = loadmat_validate(class_path, CLASSIFIER_NAME, CLASS2USE)
    cname = classfile[CLASSIFIER_NAME]
    classifier_path = os.path.join(classifier_dir,'{}.mat'.format(cname))
    if not os.path.exists(classifier_path):
        raise FileNotFoundError('classifier file {} does not exist'.format(classifier_path))
    classifier = loadmat_validate(classifier_path, CLASSES, OPT_THRESHOLDS)
    thresholds = dict(zip(classifier[CLASSES], classifier[OPT_THRESHOLDS]))
    class2useTB = classfile[CLASS2USE]
    opt_thresh = { k: thresholds[k] for k in class2useTB if k != UNCLASSIFIED }
    return opt_thresh

def summarize_counts(class_dir, thresholds, log_callback=None, ml_analyzed=None):
    """
    :param thresholds dict of thresholds by class name
    :param ml_analyzed output of summarize_ml_analyzed

    summarize class counts for an entire directory of
    class scores files and return as a json-serializable
    dict:
        {
            CLASSES: ["class1", "class2", ...],
            THRESHOLDS: {
                "class1": t1,
                "class2": t2,
                ...
            }
            LIDS: [lid1, lid2, lid3 ...],
            TIMESTAMPS: [ts1, ts2, ts3 ...], # per timestep
            COUNTS: {
                "class1": [c1, c2, c3 ...], # for class 1 per time
                "class2": [c1, c2, c3 ...], # for class 2 per time
                ...
            }
        }
    """
    if ml_analyzed is not None:
        mad = ml_analyzed2dict(ml_analyzed)

    classes = []
    timestamps = []
    counts = []
    lids = []

    for path in sorted(find_class_files(class_dir)):
        pid = Pid(path)
        if ml_analyzed is not None and pid.lid not in mad:
            continue
        if log_callback is not None:
            log_callback('{} {}'.format(pid.timestamp, pid.lid))
        timestamps.append('{}'.format(pid.timestamp))
        lids.append(pid.lid)
        scores = ClassScores(path)
        if not classes:
            classes = list(scores.class2use)
        if not counts:
            counts = { k: [] for k in classes }
        class_counts = scores.class_counts(thresholds)
        for i, k in enumerate(classes):
            counts[k].append(int(class_counts[i]))

    out = {
        THRESHOLDS: thresholds,
        LIDS: lids,
        CLASSES: classes,
        TIMESTAMPS: timestamps,
        COUNTS: counts
    }

    if ml_analyzed is not None:
        ma = [ mad.get(k,0) for k in lids ]
        out[ML_ANALYZED] = ma

    return out

def merge_ml_analyzed(count_summary, ml_analyzed_summary):
    """consumes the output of summarize_counts and summarize_ml_analyzed
    into a merged structure that is the same as the count summary except
    with an additional ml_analyzed field. modifies count_summary in place"""
    mad = ml_analyzed2dict(ml_analyzed_summary)
    ma = [ mad.get(k,0) for k in count_summary[LIDS] ]
    count_summary[ML_ANALYZED] = ma