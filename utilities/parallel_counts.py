import os
from multiprocessing import Pool
from ifcb import DataDirectory, Pid
import logging
from collections import defaultdict
import json
from argparse import ArgumentParser

from ott.common import parse_timestamps, unparse_timestamps, config_logging
from ott.class_scores import ClassScores, find_class_files, get_opt_thresh
from ott.class_scores import CLASSES, THRESHOLDS, TIMESTAMPS, LIDS, COUNTS

"""Compute counts in multiple parallel processes"""

def cc_args(class_dir, thresholds, skip=[]):
    for path in sorted(find_class_files(class_dir)):
        pid = Pid(path)
        if pid.lid in skip:
            logging.info('skipping {}'.format(pid.lid))
        else:
            yield (path, thresholds)

def cc(path_and_thresholds):
    try:
        path, thresholds = path_and_thresholds
        c = ClassScores(path)
        return path, c.class_counts(thresholds), c.class2use
    except:
        return None, None, None

if __name__=='__main__':
    ap = ArgumentParser()
    ap.add_argument('class_dir', help='directory containing class files')
    ap.add_argument('classifier_dir', help='directory containing classifier')
    ap.add_argument('-P', '--previous', help='previous output file name', default=None)
    ap.add_argument('-o', '--output', help='output file name', default='count_summary.json')
    ap.add_argument('-p', '--processes', help='Number of processes to use', default=16, type=int)
    args = ap.parse_args()

    config_logging()

    if args.previous is not None and os.path.exists(args.previous):
        logging.info('loading previous results...')
        with open(args.previous) as fin:
            previous = json.load(fin)
        lids = previous[LIDS]
        thresholds = previous[THRESHOLDS]
        classes = previous[CLASSES]
        timestamps = parse_timestamps(previous[TIMESTAMPS])
        counts = previous[COUNTS]
    else:
        logging.info('getting optimal thresholds...')
        thresholds = get_opt_thresh(args.class_dir, args.classifier_dir)
        classes = []
        counts = []
        timestamps = []
        lids = []

    logging.info('computing counts...')        

    with Pool(args.processes) as pool:
        for path, class_counts, class2use in pool.imap_unordered(cc, cc_args(args.class_dir, thresholds, skip=lids)):
            if class_counts is None:
                continue # skip skipped or failed runs
                
            pid = Pid(path)
            logging.info(path)

            lids.append(pid.lid)
            timestamps.append(pid.timestamp)

            if not classes:
                classes = list(class2use)
            if not counts:
                counts = { k: [] for k in classes }
            for i, k in enumerate(classes):
                counts[k].append(int(class_counts[i]))

    logging.info('writing summary to {}'.format(args.output))

    timestamps = unparse_timestamps(timestamps)

    summary = {
        THRESHOLDS: thresholds,
        CLASSES: classes,
        LIDS: lids,
        TIMESTAMPS: timestamps,
        COUNTS: counts
    }

    with open(args.output,'w') as fout:
        json.dump(summary, fout)
        fout.flush()
        os.fsync(fout.fileno())

    logging.info('done.')
