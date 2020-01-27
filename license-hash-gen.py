#!/usr/bin/env python
import os
import json
import subprocess
import sys

stats_json = sys.argv[1]
brpath = sys.argv[2]

start_name = sys.argv[3]

def check_license_hash(name, pkg):
    pkg_hash = os.path.join(brpath, pkg['pkg_path'], '{}.hash'.format(name))
    if pkg['license_files'] is not None:
        with open(pkg_hash) as f:
            content = f.read()
            for license in pkg['license_files']:
                if content.find(license) == -1:

                    print('check failed 1 .. file {} not in hash'.format(license))
                    return False
    else:
        return True
    return True

def get_info(name, brpath):
    try:
        output = subprocess.check_output(
                    ['make', '{}-show-info'.format(name)], cwd=brpath)
        info = json.loads(output)
    except subprocess.CalledProcessError:
        output = subprocess.check_output(
                    ['make', 'host-{}-show-info'.format(name)], cwd=brpath)
        info = json.loads(output)
        # store info as base pkg name  ... from host-<PKG> to <PKG>
        info[name] = info['host-{}'.format(name)]
    print(output)
    return (name, info)

def extract_pkg(name, brpath, source):
    pkg_dl_path = os.path.join(brpath, 'dl', name)
    output = subprocess.check_output(
            ['tar', 'xvf', source, '--strip-components=1'], cwd=pkg_dl_path)
    #print(output)

def create_hash(name, brpath, license):
    pkg_dl_path = os.path.join(brpath, 'dl', name)
    output = subprocess.check_output(
            ['sha256sum', license], cwd=pkg_dl_path)
    #print(output)
    return 'sha256  {}'.format(output)

skip_pkgs = ['android-tools', 'giblib', 'gpu-amd-bin-mx51', 'linux-headers', 'imx-gpu-viv', 'qpid-proton'
        'imx-gpu-g2d']
with open(stats_json) as f:
    pkgs = json.load(f)['packages']

    for name in pkgs:
        pkg = pkgs[name]

        if name.startswith(start_name) == False:
            continue

        print('#######', name)

        if pkg['status']['hash-license'][0] in ['ok', 'na']:
            continue

        if check_license_hash(name, pkg) == True:
            continue

        if pkg['status']['license'][0] != 'ok':
            continue
        if name in skip_pkgs:
            continue
        if name.startswith('xdriver'):
            continue
        if pkg['license_files'] is None:
            continue


        (name, info) = get_info(name, brpath)

        try:
            if len(info[name]['downloads']) == 0:
                continue
        except KeyError:
            continue

        source = info[name]['downloads'][0]['source']
        if source.endswith('zip'):
            continue

        try:
            output = subprocess.check_output(
                        ['make', '{}-legal-info'.format(name)],
                        stderr=subprocess.STDOUT,
                        cwd=brpath)
        except subprocess.CalledProcessError:
            try:
                output = subprocess.check_output(
                        ['make', 'host-{}-legal-info'.format(name)],
                        stderr=subprocess.STDOUT,
                        cwd=brpath)
            except subprocess.CalledProcessError:
                continue

        if output.find('No hash found') == -1:
            print('hash found')
            continue
        else:
            print('no hash found')

        extract_pkg(name, brpath, source)

        print(pkg)
        pkg_hash = os.path.join(brpath, pkg['pkg_path'], '{}.hash'.format(name))
        with open(pkg_hash, "a") as myfile:
            myfile.write('# locally computed\n')
            for license in pkg['license_files']:
                line = create_hash(name, brpath, license)
                myfile.write(line)



