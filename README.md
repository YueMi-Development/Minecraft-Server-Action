# Minecraft Server Action

Downloads a Minecraft server from [mcjars](https://mcjars.app), accepts the EULA, applies your
config files and runs it.

## Usage

```yaml
jobs:
  server:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - id: minecraft
        uses: YueMi-Development/Minecraft-Server-Action@v1
        with:
          server-type: PAPER
          minecraft-version: '1.21.4'
          files: |
            server.properties
            plugins/
```

Pin to `v1.0.0` instead of `v1` to pin this exact release.

## Inputs

| Input | Default | Description |
| --- | --- | --- |
| `server-type` | `PAPER` | Server type, case-insensitive. |
| `minecraft-version` | `latest` | Version, e.g. `1.21.4`, or `latest` / `latest-snapshot`. |
| `build` | `''` | Pin a build number or UUID. Empty = newest build. |
| `java-version` | `''` | Java version. Empty = detected automatically. |
| `files` | `''` | Newline-separated repo paths to copy into the server dir. |
| `server-dir` | `server` | Directory the server runs in. |
| `run-timeout` | `10m` | How long the server runs before it is stopped. |
| `min-memory` | `512M` | Initial heap size. |
| `max-memory` | `2G` | Maximum heap size. |
| `upload-artifact` | `true` | Upload the server dir as an artifact. |

## Outputs

| Output | Description |
| --- | --- |
| `build-id` | Resolved build id. |
| `build-uuid` | Resolved build UUID. |
| `java-version` | Java version used. |
| `mc-version` | Minecraft version installed. |
| `server-path` | Absolute path of the server directory. |

## Server types

`VANILLA`, `PAPER`, `PUFFERFISH`, `SPIGOT`, `FOLIA`, `PURPUR`, `WATERFALL`, `VELOCITY`,
`FABRIC`, `BUNGEECORD`, `QUILT`, `FORGE`, `NEOFORGE`, `MOHIST`, `ARCLIGHT`, `SPONGE`,
`LEAVES`, `CANVAS`, `ASPAPER`, `LEGACY_FABRIC`, `LOOHP_LIMBO`, `NANOLIMBO`, `DIVINEMC`,
`MAGMA`, `LEAF`, `VELOCITY_CTD`, `YOUER`, `PLUTO`

## Notes

- The server runs on the runner, so the world comes back as an artifact rather than persisting.
- `files` paths must exist in the repo, otherwise the job fails.
- The action writes `eula=true` before starting. Using it means accepting the
  [Minecraft EULA](https://aka.ms/MinecraftEULA).
- Linux runners only (`ubuntu-latest`).

## License

See [LICENSE](LICENSE).
