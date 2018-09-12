import os
from multiprocessing import Pool
import logging
from collections import defaultdict
import json
from argparse import ArgumentParser

from ifcb import DataDirectory

from ott.common import parse_timestamps, unparse_timestamps
from ott.ml_analyzed import LIDS, TIMESTAMPS, ML_ANALYZED, RUN_TIME, LOOK_TIME

def cma_args(dd, skip=[]):
    for bn in dd:
        if bn.lid not in skip:
            yield bn
        else:
            logging.info('skipped {}'.format(bn.lid))

def cma(bn):
    from ott.ml_analyzed import compute_ml_analyzed
    ma, rt, lt = compute_ml_analyzed(bn)
    return bn.lid, bn.timestamp, ma, rt, lt

if __name__=='__main__':
    ap = ArgumentParser()
    ap.add_argument('data_dir', help='directory containing raw data files')
    ap.add_argument('-P','--previous', help='previous output file')
    ap.add_argument('-o', '--output', help='output file name',
        default='ml_analyzed_summary.json')
    ap.add_argument('-p', '--processes', help='Number of processes to use', default=16, type=int)
    args = ap.parse_args()

    logging.basicConfig(format='%(asctime)s %(message)s',level=logging.INFO)

    dd = DataDirectory(args.data_dir)

    if args.previous is not None and os.path.exists(args.previous):
        with open(args.previous) as fin:
            summary = json.load(fin)
        summary[TIMESTAMPS] = parse_timestamps(summary[TIMESTAMPS])
    else:
        summary = defaultdict(lambda: [])

    with Pool(args.processes) as pool:
        for lid, ts, ma, rt, lt in pool.imap_unordered(cma, cma_args(dd, summary[LIDS])):
            logging.info('{} {:.3f}'.format(lid, ma))
            summary[LIDS].append(lid)
            summary[TIMESTAMPS].append(ts)
            summary[ML_ANALYZED].append(ma)
            summary[RUN_TIME].append(rt)
            summary[LOOK_TIME].append(lt)

    summary[TIMESTAMPS] = unparse_timestamps(summary[TIMESTAMPS])

    logging.info('writing {}'.format(args.output))

    with open(args.output,'w') as fout:
        json.dump(summary, fout)
        fout.flush()
        os.fsync(fout.fileno())

    logging.info('done.')