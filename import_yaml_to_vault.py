import argparse
import os
from pprint import pprint

import hvac
import yaml


# Using plaintext
# client = hvac.Client()
# client = hvac.Client(url='http://localhost:8200')
# client = hvac.Client(url='http://localhost:8200', token=os.environ['VAULT_TOKEN'])
#
# # Using TLS
# client = hvac.Client(url='https://localhost:8200')
#
# # Using TLS with client-side certificate authentication
# client = hvac.Client(url='https://localhost:8200',
#                      cert=('path/to/cert.pem', 'path/to/key.pem'))


class SpringConfigYAMLReader(object):
    """
    Read Spring Cloud Config files in YAML format
    """

    def __init__(self, input_dir, ext=".yml", verbose=False):
        self.config = {}
        self.verbose = verbose
        for filename in os.listdir(input_dir):
            if filename.endswith(ext):
                self._log('processing file: %s' % filename)
                cfg = yaml.safe_load(open(os.path.join(input_dir, filename)))
                filename_parts = filename.replace(ext, '').split('-')
                base_app = filename_parts[0]
                profile = '-'.join(filename_parts[1:])
                base_path = '/'.join([base_app, profile]) if profile else base_app
                self._log('base path: %s' % base_path)
                self.dict_path(base_path, cfg)

    def _log(self, msg):
        if self.verbose:
            print msg

    def dict_path(self, base_path, config_dict):
        for k, v in config_dict.iteritems():
            if isinstance(v, dict):
                # recurse until a value is reached
                self.dict_path('/'.join([base_path, k]), v)
            elif isinstance(v, list):
                # convert list into csv string
                # note: blindly casting list items to string
                value_list = ','.join([str(i) for i in v])
                self.dict_save(base_path, (k, value_list))
            else:
                self.dict_save(base_path, (k, v))

    def dict_save(self, route, value):
        if not self.config.get(route):
            self.config[route] = []
        self.config[route].append(value)

    def pretty_print(self):
        for route_path, kv_list in self.config.iteritems():
            print 'Spring Configuration: '
            print 'Route: %s' % route_path
            print "\tProperties:"
            for k, v in kv_list:
                print "\t\t%s=%s" % (k, v)


VAULT_BASE_ROUTE = 'secret'

if __name__ == '__main__':
    help_text = '''
        Parse Spring Config YAML files and bulk load into Vault.
    '''
    parser = argparse.ArgumentParser(
        description=help_text,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('source_dir', help='Source directory')
    parser.add_argument('--verbose', '-v', action="store_true", help='Verbose output')
    args = parser.parse_args()

    print 'Source: %s' % args.source_dir
    print 'Verbose: %s' % args.verbose
    reader = SpringConfigYAMLReader(args.source_dir)
    if args.verbose:
        reader.pretty_print()
