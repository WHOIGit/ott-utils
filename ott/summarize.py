import os
from glob import glob

import pandas as pd
import numpy as np
from scipy.io import loadmat

from ifcb.data.identifiers import Pid

class ClassScores(object):
    """represents a single class scores file"""
    def __init__(self, path):
        f = loadmat(path, squeeze_me=True)
        self.class2use = f['class2useTB']
        self.class2count = self.class2use[:-1] # exclude "unclassified"
        s = f['TBscores']
        if(len(s.shape)==1):
            s = np.array([s])
        self.scores = pd.DataFrame(s,columns=self.class2count)
    def class_counts(self, thresh={}):
        """thresh is dict mapping class name -> threshold"""
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
        counts['unclassified'] = unc_count
        # convert to array indexed by class2use
        class_counts = [counts.get(k,0) for k in self.class2use]
        return class_counts

def split_column(df, colname, names):
    """
    Convert col = [[a, b, c], [d, e, f]]
    into
    col1 = [a, d]
    col2 = [b, e]
    col3 = [c, f]
    """
    for i, name in enumerate(names):
        df[name] = [v[i] for v in df[colname]]
    df.pop(colname)
    return df

def get_opt_thresh(class_dir, classifier_dir):
    class_path = list(glob(os.path.join(class_dir,'*_class_v1.mat')))[0]
    classfile = loadmat(class_path, squeeze_me=True)
    cname = classfile['classifierName']
    classifier_path = os.path.join(classifier_dir,'{}.mat'.format(cname))
    classifier = loadmat(classifier_path, squeeze_me=True)
    maxthre = dict(zip(classifier['classes'], classifier['maxthre']))
    class2useTB = classfile['class2useTB']
    opt_thresh = {k: maxthre[k] for k in class2useTB if k != 'unclassified'}
    return opt_thresh

def summarize_counts(the_dir, thresh, log_callback=None):
    timestamps = []
    lids = []
    counts = []

    for path in glob(os.path.join(the_dir,'*_class_v1.mat')):
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