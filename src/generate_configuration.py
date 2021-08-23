import sys
import getopt
import os
import json
from . import default_configuration

def save_config(opts):
    shape_config = default_configuration.shape_config
    shape_config['save_dir'] = opts['config']['relative_path']
    shape_config['config_name'] = opts['config']['name']

    if opts['update']:
        with open(opts['config']['absolute_path'], mode='r') as fid:
            data = json.load(fid)
            shape_config.update(data)
    elif os.path.exists(opts['config']['absolute_path']):
        print("A config already exists at the specified location. Use '--update' to continue")
        sys.exit(1)
 
    if not os.path.exists(os.path.dirname(opts['config']['absolute_path'])):
        os.makedirs(os.path.dirname(opts['config']['absolute_path']))

    with open(opts['config']['absolute_path'], mode='w') as fid:
        json.dump(shape_config, fid, indent=4)
