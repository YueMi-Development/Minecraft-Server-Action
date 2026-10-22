"""Resolve a Minecraft server build from the mcjars API.

Reads its configuration from the environment (composite actions pass inputs
through ``env:``) and writes the resolved values to ``$GITHUB_OUTPUT``.
"""

import json
import os
import sys
import urllib.error
import urllib.request

API = 'https://mcjars.app/api/v1'

SERVER_TYPES = {
    'VANILLA', 'PAPER', 'PUFFERFISH', 'SPIGOT', 'FOLIA', 'PURPUR', 'WATERFALL',
    'VELOCITY', 'FABRIC', 'BUNGEECORD', 'QUILT', 'FORGE', 'NEOFORGE', 'MOHIST',
    'ARCLIGHT', 'SPONGE', 'LEAVES', 'CANVAS', 'ASPAPER', 'LEGACY_FABRIC',
    'LOOHP_LIMBO', 'NANOLIMBO', 'DIVINEMC', 'MAGMA', 'LEAF', 'VELOCITY_CTD',
    'YOUER', 'PLUTO',
}

DEFAULT_JAVA = '21'


def fail(message, detail=None):
    print(f'::error::{message}', file=sys.stderr)
    if detail:
        print(detail, file=sys.stderr)
    sys.exit(1)


def get(path):
    url = API + path
    last = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=60) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            last = f'HTTP {error.code}: ' + error.read().decode('utf-8', 'replace')
            if error.code == 404:
                break
        except Exception as error:  # noqa: BLE001 - report any transport failure alike
            last = repr(error)
    fail(f'GET {url} failed', last)


def main():
    server_type = os.environ.get('INPUT_SERVER_TYPE', '').strip().upper()
    if server_type not in SERVER_TYPES:
        fail(
            f"Unknown server type '{os.environ.get('INPUT_SERVER_TYPE', '')}'. "
            f'Valid types: {" ".join(sorted(SERVER_TYPES))}'
        )

    mc_version = os.environ.get('INPUT_MINECRAFT_VERSION', '').strip()
    if not mc_version:
        fail('minecraft-version must not be empty')

    data = get(f'/builds/{server_type}/{mc_version}')
    if not data.get('success'):
        fail(
            f'mcjars has no builds for {server_type} {mc_version}',
            json.dumps(data.get('errors', data), indent=2),
        )

    builds = data.get('builds') or []
    if not builds:
        fail(f'mcjars has no builds for {server_type} {mc_version}')

    wanted = os.environ.get('INPUT_BUILD', '').strip()
    if wanted:
        build = next(
            (
                candidate
                for candidate in builds
                if str(candidate.get('buildNumber')) == wanted
                or candidate.get('uuid') == wanted
            ),
            None,
        )
        if build is None:
            fail(f"No build matching '{wanted}' for {server_type} {mc_version}")
    else:
        # The API returns builds newest first.
        build = builds[0]

    concrete_version = build.get('versionId') or ''

    java_version = os.environ.get('INPUT_JAVA_VERSION', '').strip()
    if not java_version:
        if concrete_version:
            version_data = get(f'/version/{concrete_version}')
            java_version = str((version_data.get('version') or {}).get('java') or '')
        if not java_version:
            print(
                '::warning::Could not detect the required Java version, '
                f'falling back to {DEFAULT_JAVA}'
            )
            java_version = DEFAULT_JAVA

    server_dir = os.environ.get('INPUT_SERVER_DIR', '').strip() or 'server'
    server_path = os.path.abspath(server_dir)

    outputs = {
        'build-id': build.get('id'),
        'build-uuid': build.get('uuid'),
        'java-version': java_version,
        'mc-version': concrete_version,
        'server-path': server_path,
    }

    with open(os.environ['GITHUB_OUTPUT'], 'a', encoding='utf-8') as output_file:
        for key, value in outputs.items():
            output_file.write(f'{key}={value}\n')

    print(f'Server type : {server_type}')
    print(f"Build       : {build.get('name')} (id {build.get('id')})")
    print(f'MC version  : {concrete_version}')
    print(f'Java        : {java_version}')
    print(f'Server path : {server_path}')


if __name__ == '__main__':
    main()
