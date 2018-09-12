import json
import sys
from argparse import ArgumentParser
import logging

from ott.class_scores import merge_ml_analyzed
from ott.class_summary import ClassSummary 
from ott.common import config_logging

"""Given a count summary and ml_analyzed summary, merge the two so that
the count summary contains the ml_analyzed data, this is necessary for
producing concentrations product."""

if __name__=='__main__':
    ap = ArgumentParser()
    ap.add_argument('count_summary', help='count summary json file')
    ap.add_argument('ml_analyzed_summary', help='ml_analyzed summary json file')
    ap.add_argument('-o', '--output', help='output file')
    args = ap.parse_args()

    config_logging()
    
    with open(args.ml_analyzed_summary) as fin:
        ml_analyzed = json.load(fin)

    with open(args.count_summary) as fin:
        count_summary = json.load(fin)

    logging.info('merging ml_analyzed with counts')

    merge_ml_analyzed(count_summary, ml_analyzed)

    # if an output file is specified, write to that file.
    # otherwise overwrite the existing count summary with the
    # summary containing the ml_analyzed data

    if args.output is None:
        with open(args.count_summary,'w') as fout:
            json.dump(count_summary, fout)
    else:
        with open(args.output,'w') as fout:
            json.dump(count_summary, fout)
