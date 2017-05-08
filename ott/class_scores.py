import os
from glob import glob

import pandas as pd
import numpy as np
from scipy.io import loadmat

from ifcb.data.identifiers import Pid

from .common import loadmat_validate, split_column
from .common import CLASS2USE, UNCLASSIFIED

SCORES = 'TBscores'
CLASSIFIER_NAME = 'classifierName'
OPT_THRESHOLDS = 'maxthre'
CLASSES = 'classes'

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

def get_opt_thresh(class_dir, classifier_dir):
    try:
        # pick the first one, because it doesn't matter which one we pick
        class_path = list(glob(os.path.join(class_dir, CLASS_GLOB)))[0]
    except IndexError:
        raise FileNotFoundError('no class score files found in {}'.format(class_dir))
    classfile = loadmat_validate(class_path, CLASSIFIER_NAME, CLASS2USE)
    cname = classfile[CLASSIFIER_NAME]
    classifier_path = os.path.join(classifier_dir,'{}.mat'.format(cname))
    classifier = loadmat_validate(classifier_path, CLASSES, OPT_THRESHOLDS)
    thresholds = dict(zip(classifier[CLASSES], classifier[OPT_THRESHOLDS]))
    class2useTB = classfile[CLASS2USE]
    opt_thresh = {k: thresholds[k] for k in class2useTB if k != UNCLASSIFIED}
    return opt_thresh

def summarize_counts(the_dir, thresh, log_callback=None):
    """summarize class counts for an entire directory of
    class scores files and return as a pandas dataframe"""
    timestamps = []
    lids = []
    counts = []

    for path in glob(os.path.join(the_dir, CLASS_GLOB)):
        pid = Pid(path)
        if log_callback is not None:
            log_callback('{} {}'.format(pid.timestamp, pid.lid))
        timestamps.append(pid.timestamp)
        lids.append(pid.lid)
        scores = ClassScores(path)
        class2use = scores.class2use
        class_counts = scores.class_counts(thresh)
        counts.append(class_counts)

    df = pd.DataFrame({
        'lid': lids,
        'counts': counts
    },index=timestamps)

    df = split_column(df,'counts',class2use)

    return df

def summary2mat(df):
    """convert the results of summarize_counts to a class summary
    matlab file that can be consumed by ClassSummary"""
    pass