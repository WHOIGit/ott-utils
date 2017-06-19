from multiprocessing import Pool
from ifcb import DataDirectory, Pid
import logging
from collections import defaultdict
import json
from argparse import ArgumentParser

from ott.common import unparse_timestamps
from ott.class_scores import ClassScores, find_class_files, get_opt_thresh
from ott.class_scores import CLASSES, THRESHOLDS, TIMESTAMPS, LIDS, COUNTS

def cc_args(class_dir, thresholds):
    for path in sorted(find_class_files(class_dir)):
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
    ap.add_argument('-o', '--output', help='output file name', default='count_summary.json')
    ap.add_argument('-p', '--processes', help='Number of processes to use', default=16)
    args = ap.parse_args()

    logging.basicConfig(format='%(asctime)s %(message)s',level=logging.INFO)

    logging.info('getting optimal thresholds...')
    thresholds = get_opt_thresh(args.class_dir, args.classifier_dir)

    logging.info('computing counts...')

    classes = []
    counts = []
    timestamps = []
    lids = []

    with Pool(16) as pool:
        for path, class_counts, class2use in pool.imap_unordered(cc, cc_args(args.class_dir, thresholds)):
            if class_counts is None:
                continue # skip failed runs
                
            logging.info(path)
            pid = Pid(path)
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

    logging.info('done.')