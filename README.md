# Minecraft Server CI

A custom GitHub Action that downloads a Minecraft server jar from
[mcjars](https://mcjars.app), accepts the EULA, copies configuration files from your
repository into the server directory, and runs the server — streaming the console log into
the Actions log and uploading the server directory as an artifact.

## Usage

### In another repository

```yaml
name: Minecraft

on:
  push:
    branches: [main]

jobs:
  server:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - id: minecraft
        uses: OWNER/Minecraft-Server-CI@v1
        with:
          server-type: PAPER
          minecraft-version: '1.21.4'
          files: |
            server.properties
            plugins/

      - name: Show what was installed
        run: echo "Build ${{ steps.minecraft.outputs.build-id }} on Java ${{ steps.minecraft.outputs.java-version }}"
```

### In this repository

Use the relative path to the action:

```yaml
- uses: ./
  with:
    server-type: PAPER
```

## Inputs

| Input | Type | Default | Description |
| --- | --- | --- | --- |
| `server-type` | string | `PAPER` | Server type. Case-insensitive. See the list below. |
| `minecraft-version` | string | `latest` | Minecraft version (e.g. `1.21.4`), or `latest` / `latest-snapshot`. |
| `build` | string | `''` | Pin a specific build number (e.g. `232`) or build UUID. Empty = newest build. |
| `java-version` | string | `''` | Java version override. Empty = detected automatically from the Minecraft version. |
| `files` | string | `''` | Newline-separated, repo-relative paths to copy into the server directory. |
| `server-dir` | string | `server` | Directory the server is installed into and runs from. |
| `run-timeout` | string | `10m` | How long the server may run before it is stopped gracefully. |
| `min-memory` | string | `512M` | Initial JVM heap size. |
| `max-memory` | string | `2G` | Maximum JVM heap size. |
| `upload-artifact` | string | `true` | Upload the server directory (logs, world, config) as an artifact. |

## Outputs

| Output | Description |
| --- | --- |
| `build-id` | Numeric id of the resolved mcjars build. |
| `build-uuid` | UUID of the resolved mcjars build. |
| `java-version` | Java version the server requires. |
| `mc-version` | Concrete Minecraft version that was installed. |
| `server-path` | Absolute path of the server directory. |

## Server types

`VANILLA`, `PAPER`, `PUFFERFISH`, `SPIGOT`, `FOLIA`, `PURPUR`, `WATERFALL`, `VELOCITY`,
`FABRIC`, `BUNGEECORD`, `QUILT`, `FORGE`, `NEOFORGE`, `MOHIST`, `ARCLIGHT`, `SPONGE`,
`LEAVES`, `CANVAS`, `ASPAPER`, `LEGACY_FABRIC`, `LOOHP_LIMBO`, `NANOLIMBO`, `DIVINEMC`,
`MAGMA`, `LEAF`, `VELOCITY_CTD`, `YOUER`, `PLUTO`

Not every type has builds for every Minecraft version. If none exist the action fails with the
API's error message rather than starting a broken server.

## Copying files

The `files` input takes one repository-relative path per line. Directories are copied
recursively. Files are copied **after** the server jar is downloaded and **before** the server
starts, so your files take precedence over the server's generated defaults:

```yaml
files: |
  server.properties
  spigot.yml
  plugins/
  config/permissions.yml
```

A path that does not exist in the repository fails the job — a silently skipped config file is
worse than a loud failure.

## EULA

The action writes `eula.txt` containing `eula=true` into the server directory before the server
starts, so the server proceeds straight to startup instead of stopping to ask for acceptance.
By using this action you accept the [Minecraft EULA](https://aka.ms/MinecraftEULA) on behalf of
your organization.

## How the jar is downloaded

The action does not construct download URLs itself. It asks mcjars to resolve the requested
server type and version into a build, then fetches the install script mcjars generates for that
build and runs it:

```
GET /api/v1/builds/{type}/{version}     -> resolve the build
GET /api/v1/script/{build}/bash        -> generated install script
```

Using the generated script is what makes modded server types work: a Forge build is a 96 MB zip
that has to be unpacked alongside a `libraries/` tree, not a plain jar, and the script already
encodes the correct download/unzip/remove sequence.

Forge is launched through the `unix_args.txt` that ships inside its installation
(`java @libraries/net/minecraftforge/forge/*/unix_args.txt nogui`); every other server type is
launched with `java -jar server.jar nogui`.

The Java version is read from `GET /api/v1/version/{version}` and installed with
`actions/setup-java`. Override it with the `java-version` input if you need to pin a patch
release.

## Notes and limitations

- The server runs on the GitHub runner, not on a persistent host. The world is saved when the
  server is stopped and comes back as an artifact — it is not a live, stateful world.
- The server is stopped gracefully once `run-timeout` elapses, so the world is flushed to disk.
- Forge's first launch re-installs the mod loader and takes considerably longer than other server
  types; give it a longer `run-timeout` if it does not finish in time.
- Only one server runs per job. Running several requires several job invocations.
- The mcjars API rate-limits at 120 requests per minute. This action makes two requests per run,
  so it stays well inside the limit.
- The action is written for Linux runners (`ubuntu-latest`); the server download and launch steps
  assume a POSIX shell.

## License

See [LICENSE](LICENSE).
