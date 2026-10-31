# Token Meter flake

Nix packaging for [splunk/token-meter](https://github.com/splunk/token-meter).
The upstream source and nixpkgs revisions are pinned in `flake.lock`.
Supports Apple Silicon/Intel macOS and aarch64/x86_64 Linux.

## Run

```sh
nix run
```

Open <http://127.0.0.1:8722>. Stop with Ctrl-C. The server reads your local
agent session data and keeps its settings and state under `~/.token-meter`
(with upstream's XDG paths used where applicable).

This package runs the dashboard backend. Native menu-bar/tray companions and
automatic startup are not configured by this flake.

The MCP server is also available:

```sh
nix run .#mcp
```

## Build and check

```sh
nix build
nix flake check
```

The package provides `token-meter` and `token-meter-mcp` in `result/bin`.
The check imports both Python entry points and verifies the dashboard assets.

## Update

```sh
nix flake update token-meter
nix build
nix flake check
```

Use Nix to update this installation rather than the upstream installer/updater.
