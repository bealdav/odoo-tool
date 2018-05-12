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


SRC_DIRS = ('external-src', 'parts')
odoo_conf = 'etc/openerp.cfg'

if os.path.isdir(SRC_DIRS[0]):
    TYPE = 'buildin'
    SRC_DIR = SRC_DIRS[0]
    EXCL_PATHS = (
        'odoo/addons',
        'modules',
        '%s' % MIGRATED)
elif os.path.isdir(SRC_DIRS[1]):
    TYPE = 'buildout'
    SRC_DIR = SRC_DIRS[1]
    EXCL_PATHS = (
        '/workspace/parts/odoo/addons',
        '/workspace/modules',
        '/workspace/%s' % MIGRATED)
else:
    print("No matching folder '%s' in current path." % SRC_DIRS)

MIGR_VERSION = 10


def get_immediate_subdirectories(a_dir):
    return [name for name in os.listdir(a_dir)
            if os.path.isdir(os.path.join(a_dir, name))]


def get_subdirectories_in_src(odoo_conf=odoo_conf):
    """ extract addons_path from Odoo config
    """
    config = configparser.ConfigParser()
    config.read(odoo_conf)
    addons_path = config['options']['addons_path']
    if not config['options'].get('original_addons_path'):
        ''
        # set_original_addons_path(addons_path, config)
    if config['options'].get('original_addons_path'):
        # we manually saved old addons path in dedicated key
        addons_path = config['options']['original_addons_path']
    paths = [x for x in addons_path.split(',')
             if EXCL_PATHS[0] not in x and
             EXCL_PATHS[1] not in x and EXCL_PATHS[2] not in x]
    paths = [x.replace('/workspace/', '') for x in paths]
    return paths


def set_original_addons_path(addons_path, config):
    config['options']['original_addons_path'] = addons_path
    config.write(odoo_conf)


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
        if TYPE == 'buildin':
            src = '%s/%s' % (path, module)
        else:
            src = '../%s/%s' % (path, module)
        subprocess.run(['ln', '-s', src, MIGRATED])


def choose_version(version=MIGR_VERSION):
    valid = False
    alert = ("'%s' version you specified is not valid: "
             "required from 9 to 20")
    while not valid:
        print("Define migration script you want to search: 9, 10, 11, etc")
        version = input("(Default one is '%s')\n"
                        "Your version here: " % MIGR_VERSION)
        if not version:
            version = MIGR_VERSION
            valid = True
        elif not version.isdigit():
            valid = False
        elif int(version) not in range(9, 50):
            valid = False
        else:
            valid = True
        if not valid:
            print(alert % version)
            return False
        return version


def set_odoo_conf_path():
    valid = False
    alert = ("'%s' is not a valid path !")
    while not valid:
        path = input("Define odoo conf path from here: ")
        if not os.path.isfile(path):
            print(alert % '%s%s' % (os.getcwd(), path))
            return False
        return path


def main(odoo_conf, version=MIGR_VERSION):
    created_links = []
    if not os.path.exists(MIGRATED):
        subprocess.run(['mkdir', MIGRATED])
    else:
        subprocess.run(['find', MIGRATED, '-type', 'l', '-delete'])
    paths = get_subdirectories_in_src(odoo_conf=odoo_conf)
    for path in paths:
        modules = get_modules2link(path, version=version)
        modules = [x for x in modules if x not in created_links]
        created_links.extend(modules)
        if modules:
            print("Found modules with migration script: %s" % modules)
            generate_module_links(path, modules)


if __name__ == '__main__':
    print(DOC)
    if TYPE == 'buildin':
        # Odoo file is in an unpredictable place
        odoo_conf = set_odoo_conf_path()
    # Odoo version
    version = choose_version()

    if odoo_conf and version:
        main(odoo_conf, version=version)
        print("Success ! \n\n"
              "'%s' folder has been created/updated with modules\n"
              "with migration script in '%s' version.\n"
              "Manual operation to do:\n"
              "Ensure you created 'original_addons_path' key in your "
              "file odoo config by duplicated addons_path key and"
              "rewrite addons_path with no more repos than:"
              "\nodoo, custom modules and %s" %
              (MIGRATED, version, MIGRATED))
