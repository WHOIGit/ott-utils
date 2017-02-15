import sys
import os

import yaml
from munch import munchify

sys.path.append('netcdf-cf-utils')

from ott.netcdf import IfcbMetadata, csdir2netcdf

# constants
CONFIG_FILE = 'config.yml'

def load_config(config_file):
    with open(config_file) as fin:
        return munchify(yaml.safe_load(fin))

def process_dir(in_dir, out_dir):
    # load configuration
    config = load_config(CONFIG_FILE)

    # configure metadata
    md = IfcbMetadata(**config.metadata)

    # configure summary processing
    freq = config.summary.frequency
    thresh = config.summary.threshold

    try:
        os.makedirs(out_dir)
    except:
        pass

    csdir2netcdf(in_dir, out_dir, frequency=freq, threshold=thresh, metadata=md)

if __name__=='__main__':
    assert len(sys.argv) == 3, "must specify an input and output directory"
    in_dir = sys.argv[1]
    out_dir = sys.argv[2]
    process_dir(in_dir, out_dir)
