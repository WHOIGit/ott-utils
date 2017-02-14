import os
import re

import netCDF4 as nc4

from nccf.timeseries import TimeseriesWriter

from .class_summary import ClassSummary

MVCO_ASIT_LAT=41.325
MVCO_ASIT_LON=-70.5667
MVCO_IFCB_DEPTH=4

MVCO_ASIT_NAME = 'MVCO ASIT'
IFCB_NAME = 'Imaging FlowCytobot'

MVCO_IFCB_INSTITUTION='WHOI'

class IfcbMetadata(object):
    def __init__(self, lat=MVCO_ASIT_LAT, lon=MVCO_ASIT_LON,
                 depth=MVCO_IFCB_DEPTH, platform_name=MVCO_ASIT_NAME,
                 instrument_name=IFCB_NAME, institution=MVCO_IFCB_INSTITUTION):
        self.lat = lat
        self.lon = lon
        self.depth = depth
        self.platform_name = platform_name
        self.instrument_name = instrument_name
        self.institution = institution

def cs2netcdf(cs_path, nc_path, frequency=None, metadata=IfcbMetadata()):
    cs = ClassSummary(cs_path)
    conc = cs.concentrations(frequency=frequency)
    g_attrs = {
        'title': 'Phytoplankton concentration (IFCB)',
        'summary': 'Phytoplankton concentration by class derived from images collected by Imaging FlowCytobot',
        'institution': metadata.institution
    }
    i_attrs = {
        'long_name': metadata.instrument_name
    }
    p_attrs = {
        'long_name': metadata.platform_name
    }
    with nc4.Dataset(nc_path,'w') as ds:
        tw = TimeseriesWriter(ds)
        tw.from_dataframe(conc, lat=metadata.lat, lon=metadata.lon,
                          global_attributes=g_attrs,
                          platform_attributes=p_attrs,
                          instrument_attributes=i_attrs)

def csdir2netcdf(cs_dir, nc_dir, frequency=None, metadata=IfcbMetadata()):
    for fn in os.listdir(cs_dir):
        if re.match(r'summary_allTB\d{4}\.mat',fn):
            cs_path = os.path.join(cs_dir, fn)
            nc_fn = re.sub(r'\.mat$','.nc',fn)
            nc_path = os.path.join(nc_dir, nc_fn)
            cs2netcdf(cs_path, nc_path, frequency=frequency, metadata=metadata)
