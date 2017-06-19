from argparse import ArgumentParser
import json

import yaml
from munch import munchify

from ott.netcdf import IfcbMetadata, cs2netcdf

def load_config(config_file):
    with open(config_file) as fin:
        return munchify(yaml.safe_load(fin))

if __name__=='__main__':
    ap = ArgumentParser()
    ap.add_argument('count_summary', help='count summary JSON file')
    ap.add_argument('output', help='output NetCDF file')
    ap.add_argument('-c', '--config', help='configuration file', default='config.yml')
    args = ap.parse_args()

    # load configuration
    config = load_config(args.config)

    # configure metadata
    md = IfcbMetadata(**config.metadata)

    # load count summary (must have ml_analyzed)
    with open(args.count_summary) as fin:
        counts = json.load(fin)

    if not 'ml_analyzed' in counts:
        raise ValueError('counts must contain ml_analyzed')

    frequency = config.summary.frequency

    cs2netcdf(args.count_summary, args.output, frequency=frequency, metadata=md)
