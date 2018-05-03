#!/usr/bin/env python3

import os
import configparser
import subprocess

MIGRATED = 'MIGRATED_MODULES'

DOC = """
What this script do ?
---------------------
It links modules with an existing migration
for a target odoo version to %s folder

Then you may use this folder as addons path
replacement to only execute migrated code

=====================================================

""" % MIGRATED

SRC_DIR = './parts'
ODOO_CONF = 'etc/openerp.cfg'
MIGR_VERSION = 9


def get_immediate_subdirectories(a_dir):
    return [name for name in os.listdir(a_dir)
            if os.path.isdir(os.path.join(a_dir, name))]


def get_subdirectories_in_parts(odoo_cfg=ODOO_CONF):
    """ extract addons_path from Odoo config
    """
    config = configparser.ConfigParser()
    config.read(odoo_cfg)
    addons_path = config['options']['addons_path']
    paths = [x for x in addons_path.split(',')
             if x not in (
                 '/workspace/parts/odoo/addons',
                 '/workspace/modules',
                 '/workspace/%s' % MIGRATED)]
    paths = [x.replace('/workspace/', '') for x in paths]
    return paths


def get_modules2link(path, version=MIGR_VERSION):
    """
    """
    modules = get_immediate_subdirectories(path)
    modules2link = []
    for module in modules:
        module_path = '%s/%s' % (path, module)
        migr_path = '%s/migrations' % (module_path)
        if os.path.isdir(migr_path):
            migr_folder = get_immediate_subdirectories(migr_path)
            migr_vers = [x.split('.')[0] for x in migr_folder]
            if str(version) in migr_vers:
                modules2link.append(module)
    return modules2link


def generate_module_links(path, modules):
    """ Link modules to migrated folder
    """
    for module in modules:
        src = '../%s/%s' % (path, module)
        subprocess.run(['ln', '-s', src, MIGRATED])


def main(version=MIGR_VERSION):
    created_links = []
    if not os.path.exists(MIGRATED):
        subprocess.run(['mkdir', MIGRATED])
    else:
        subprocess.run(['find', MIGRATED, '-type', 'l', '-delete'])
    paths = get_subdirectories_in_parts()
    for path in paths:
        modules = get_modules2link(path, version=version)
        print("Found modules: %s" % modules)
        modules = [x for x in modules if x not in created_links]
        created_links.extend(modules)
        if modules:
            generate_module_links(path, modules)


if __name__ == '__main__':
    print(DOC)
    main()
    print("Success ! \n\n"
          "'%s' folder has been created/updated.\n"
          "Manual operation to do:\n"
          "Ensure your addons_path "
          "has no more repo than:\nodoo, custom modules and %s" %
          (MIGRATED, MIGRATED))
