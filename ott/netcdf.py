import os
import re

import netCDF4 as nc4
import numpy as np

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

CONC_TITLE='Phytoplankton concentration (IFCB)'
CONC_SUMMARY='Phytoplankton concentration by class '\
         'derived from images collected by '\
         'Imaging FlowCytobot'

COUNT_TITLE='Phytoplankton counts (IFCB)'
COUNT_SUMMARY='Phytoplankton counts by class '\
         'derived from images collected by '\
         'Imaging FlowCytobot'

class IfcbMetadata(object):
    """Represents metadata describing IFCB deployment.
    Default values are relevant to WHOI/MVCO deployment"""
    def __init__(self, latitude=MVCO_ASIT_LAT, longitude=MVCO_ASIT_LON,
                 depth=MVCO_IFCB_DEPTH, platform_name=MVCO_ASIT_NAME,
                 instrument_name=IFCB_NAME, institution=MVCO_IFCB_INSTITUTION,
                 title=CONC_TITLE, summary=CONC_SUMMARY):
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
                'institution': self.institution,
                'cdm_data_type': 'timeSeries',
                'cdm_timeseries_variables': 'station, latitude, longitude, z',
                'subsetVariables': 'z'
            },
            'platform': {
                'long_name': self.platform_name
            },
            'instrument': {
                'long_name': self.instrument_name
            }
        }

class ClassSummaryOutput(ClassSummary):
    def __init__(self, file, metadata=IfcbMetadata()):
        super(ClassSummaryOutput, self).__init__(file)
        self.metadata = metadata
    def get_product(self, product='concentrations', frequency=None):
        assert product in ['concentrations', 'counts']
        if product == 'concentrations':
            return self.concentrations(frequency)
        elif product == 'counts':
            return self.counts(frequency)
    def get_dsxml(self, product, nc_path):
        nc_dir = os.path.abspath(os.path.dirname(nc_path))
        dataset_xml = generate_datasets_xml(nc_dir, self.metadata, product)
        return dataset_xml
    def write_netcdf(self, product, nc_path):
        attrs = self.metadata.get_attributes()
        product = product.copy()
        product['y'] = self.metadata.latitude
        product['x'] = self.metadata.longitude
        product['z'] = self.metadata.depth
        product['t'] = product.index
        product['station'] = self.metadata.platform_name
        ds = OrthogonalMultidimensionalTimeseries.from_dataframe(product, nc_path, attributes=attrs)
        ds.close()
        ds = nc4.Dataset(nc_path,'a')
        # now add class labels and thresholds
        classes = self.classes
        ds.createDimension('classes', len(classes))
        class_labels_var = ds.createVariable('class_labels',str,'classes')
        for i, c in enumerate(classes):
            class_labels_var[i] = c
        thresholds = self.thresholds
        thresholds_var = ds.createVariable('thresholds',float,'classes')
        for i, claz in enumerate(classes):
            thresholds_var[i] = thresholds.get(claz,np.nan)
        ds.close()