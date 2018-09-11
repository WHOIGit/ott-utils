import random
from jinja2 import Environment, PackageLoader, select_autoescape

"""
dataset_id
directory
creator_name
summary
title
varnames (list of variable names for phyto classes)
"""

def gen_id(pfx):
    v = random.randint(0,2**32)
    return '{}_{:x}'.format(pfx,v)

def generate_datasets_xml(directory, metadata, conc):
    env = Environment(
        loader = PackageLoader('ott','resources'),
        autoescape = select_autoescape('xml')
    )
    template = env.get_template('dataset.xml')
    context = {
        'dataset_id': gen_id('ifcb'),
        'directory': directory,
        'creator_name': metadata.institution,
        'title': metadata.title,
        'summary': metadata.summary,
        'varnames': conc.columns
    }
    return template.render(**context)

    
    
