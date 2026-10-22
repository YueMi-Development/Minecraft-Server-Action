"""Resolve a Minecraft server build from the mcjars API.

Reads its configuration from the environment (composite actions pass inputs
through ``env:``) and writes the resolved values to ``$GITHUB_OUTPUT``. The
installation steps are written next to the server so the install script can
replay them.
"""

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

API = 'https://mcjars.app/api/v3'

DEFAULT_JAVA = '21'


def fail(message, detail=None):
    print(f'::error::{message}', file=sys.stderr)
    if detail:
        print(detail, file=sys.stderr)
    sys.exit(1)


def get(path, query=None):
    url = API + path
    if query:
        url += '?' + urllib.parse.urlencode(query, doseq=True)

    last = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=60) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            body = error.read().decode('utf-8', 'replace')
            last = f'HTTP {error.code}: {body}'
            if error.code == 404:
                break
        except Exception as error:  # noqa: BLE001 - report any transport failure alike
            last = repr(error)
    fail(f'GET {url} failed', last)


def api_errors(payload):
    errors = payload.get('errors')
    if isinstance(errors, list):
        return '\n'.join(str(item) for item in errors)
    return json.dumps(payload, indent=2)


def find_build_by_name(server_type, mc_version, name):
    """Look up a build by its name, e.g. ``#232``."""
    query = [('page', 1), ('per_page', 20), ('search', name.lstrip('#'))]
    data = get(f'/builds/types/{server_type}/versions/{mc_version}', query)
    builds = (data.get('builds') or {}).get('data') or []
    for build in builds:
        if build.get('name') == name or str(build.get('name', '')).lstrip('#') == name.lstrip('#'):
            return build
    return None


def main():
    server_type = os.environ.get('INPUT_SERVER_TYPE', '').strip()
    if not server_type:
        fail('server-type must not be empty')

    mc_version = os.environ.get('INPUT_MINECRAFT_VERSION', '').strip()
    if not mc_version:
        fail('minecraft-version must not be empty')

    wanted = os.environ.get('INPUT_BUILD', '').strip()

    build = None
    version = None

    if wanted:
        # A build is addressed either by its uuid or by its name.
        if wanted.lower().startswith('#') or wanted.isdigit():
            build = find_build_by_name(server_type, mc_version, wanted)
            if build is None:
                fail(f"No build matching '{wanted}' for {server_type} {mc_version}")
        else:
            data = get(f'/builds/{wanted}')
            build = data.get('build')
            version = data.get('version')
            if not build:
                fail(f'No build found for uuid {wanted}', api_errors(data))
    else:
        data = get(f'/builds/types/{server_type}/versions/{mc_version}/latest')
        build = data.get('build')
        if not build:
            fail(f'mcjars has no builds for {server_type} {mc_version}', api_errors(data))

    build_uuid = build.get('uuid')

    # The latest endpoint only returns the build, so ask for it again by uuid to
    # pick up the version details (which carry the required Java version).
    if version is None:
        version = get(f'/builds/{build_uuid}').get('version') or {}

    java_version = os.environ.get('INPUT_JAVA_VERSION', '').strip()
    if not java_version:
        java_version = str(version.get('java') or '')
        if not java_version:
            print(
                '::warning::Could not detect the required Java version, '
                f'falling back to {DEFAULT_JAVA}'
            )
            java_version = DEFAULT_JAVA

    server_dir = os.environ.get('INPUT_SERVER_DIR', '').strip() or 'server'
    server_path = os.path.abspath(server_dir)

    outputs = {
        'build-id': build_uuid,
        'build-uuid': build_uuid,
        'java-version': java_version,
        'mc-version': build.get('version_id') or version.get('id') or '',
        'server-path': server_path,
    }

    with open(os.environ['GITHUB_OUTPUT'], 'a', encoding='utf-8') as output_file:
        for key, value in outputs.items():
            output_file.write(f'{key}={value}\n')

    # Hand the installation steps to the install script.
    os.makedirs(server_path, exist_ok=True)
    steps_file = os.path.join(server_path, '.mcjars-installation.json')
    with open(steps_file, 'w', encoding='utf-8') as steps_out:
        json.dump(build.get('installation') or [], steps_out)

    print(f'Server type : {server_type}')
    print(f"Build       : {build.get('name')} ({build_uuid})")
    print(f"MC version  : {outputs['mc-version']}")
    print(f'Java        : {java_version}')
    print(f'Server path : {server_path}')


if __name__ == '__main__':
    main()
