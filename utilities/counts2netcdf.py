from argparse import ArgumentParser
import json
import logging

import yaml
from munch import munchify

from ott.class_summary import ClassSummary
from ott.netcdf import IfcbMetadata, get_c_or_c, c_or_c2netcdf, add_thresholds
from ott.common import config_logging

def load_config(config_file):
    with open(config_file) as fin:
        return munchify(yaml.safe_load(fin))

if __name__=='__main__':
    ap = ArgumentParser()
    ap.add_argument('count_summary', help='count summary JSON file')
    ap.add_argument('output', help='output NetCDF file')
    ap.add_argument('-d', '--dataset', help='output datasets.xml file', default=None)
    ap.add_argument('-c', '--config', help='configuration file', default='config.yml')
    args = ap.parse_args()

    config_logging()

    # load configuration
    config = load_config(args.config)

    # configure metadata
    md = IfcbMetadata(**config.metadata)

    # load count summary (must have ml_analyzed)
    with open(args.count_summary) as fin:
        counts = json.load(fin)

    product = config.summary.product
    assert product in ['counts', 'concentrations'], 'product must be either counts or concentrations'

    if product == 'concentrations' and not 'ml_analyzed' in counts:
        raise ValueError('counts must contain ml_analyzed')

    frequency = config.summary.frequency

    logging.info('writing summary output to {}'.format(args.output))

    cs = ClassSummary(args.count_summary)
    c_or_c = get_c_or_c(cs, frequency, product=product)
    c_or_c2netcdf(c_or_c, args.output, args.dataset, metadata=md)
    add_thresholds(cs, args.output)

    logging.info('done.')