import os
import re

import netCDF4 as nc4

from pocean.dsg.timeseries.om import OrthogonalMultidimensionalTimeseries

from .class_summary import ClassSummary
from .erddap import generate_datasets_xml

# default metadata values describe WHOI/MVCO deployment
# the recommended way to override these is using config.yml

MVCO_ASIT_LAT=41.325
MVCO_ASIT_LON=-70.5667
MVCO_IFCB_DEPTH=4

MVCO_ASIT_NAME = 'MVCO ASIT'
IFCB_NAME = 'Imaging FlowCytobot'

MVCO_IFCB_INSTITUTION='WHOI'

TITLE='Phytoplankton concentration (IFCB)'
SUMMARY='Phytoplankton concentration by class '\
         'derived from images collected by '\
         'Imaging FlowCytobot'

class IfcbMetadata(object):
    """Represents metadata describing IFCB deployment.
    Default values are relevant to WHOI/MVCO deployment"""
    def __init__(self, latitude=MVCO_ASIT_LAT, longitude=MVCO_ASIT_LON,
                 depth=MVCO_IFCB_DEPTH, platform_name=MVCO_ASIT_NAME,
                 instrument_name=IFCB_NAME, institution=MVCO_IFCB_INSTITUTION,
                 title=TITLE, summary=SUMMARY):
        self.latitude = latitude
        self.longitude = longitude
        self.depth = depth
        self.platform_name = platform_name
        self.instrument_name = instrument_name
        self.title = title
        self.summary = summary
        self.institution = institution
    def get_attributes(self):
        return {
            'global': {
                'title': self.title,
                'summary': self.summary,
                'institution': self.institution
            },
            'platform': {
                'long_name': self.platform_name
            },
            'instrument': {
                'long_name': self.instrument_name
            }
        }

def cs2netcdf(cs_path, nc_path, frequency=None, metadata=IfcbMetadata()):
    """Convert a class summary to netcdf
    :param cs_path: path of class summary json file
    :param nc_path: path of output .nc file
    :param frequency: binning frequency for concentrations (None for no binning)
    :param metadata: metadata attributes (default will use hardcoded WHOI/MVCO values)
    :returns a datasets.xml snippet for ERDDAP
    """
    cs = ClassSummary(cs_path)
    conc = cs.concentrations(frequency=frequency)
    attrs = metadata.get_attributes()

    dataset_xml = generate_datasets_xml(os.path.abspath(os.path.dirname(nc_path)), metadata, conc)
    
    # set up dataframe for pocean
    conc['y'] = metadata.latitude
    conc['x'] = metadata.longitude
    conc['z'] = metadata.depth
    conc['t'] = conc.index
    conc['station'] = metadata.platform_name
    
    OrthogonalMultidimensionalTimeseries.from_dataframe(conc, nc_path, attributes=attrs)

    return dataset_xml

def list_csdir(cs_dir):
    """given a directory, list all summary_allTB\d+.mat files"""
    for fn in os.listdir(cs_dir):
        if re.match(r'summary_allTB\d+\.mat',fn):
            yield os.path.join(cs_dir, fn)
    
def csdir2netcdf(cs_dir, nc_dir, frequency=None, metadata=IfcbMetadata()):
    """convert a directory of class summary files to nc files.
    see cs2netcdf. will write a datasets.xml snippet to the output directory"""
    for cs_path in list_csdir(cs_dir):
        fn = os.path.basename(cs_path)
        nc_fn = re.sub(r'\.mat$','.nc',fn)
        nc_path = os.path.join(nc_dir, nc_fn)
        ds_xml = cs2netcdf(cs_path, nc_path, frequency=frequency, metadata=metadata)
        with open(os.path.join(nc_dir,'dataset.xml'),'w') as fout:
            fout.write(ds_xml)
