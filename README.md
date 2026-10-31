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
It also exercises Ollama setup, Nix-managed updates, and the MCP launcher with
no Python available on `PATH`. The launcher used by Settings → MCP uses the
same pinned Python as the command-line entry point.

## Ollama for Work insights (macOS)

This package patches Work insights to use the Ollama CLI from the pinned
nixpkgs revision. It never downloads an Ollama runtime, starts a private
fallback server, or replaces the configured server address.

An existing compatible Ollama server can be reused. To run the Nix-packaged
server instead, start it separately before enabling Work insights:

```sh
nix run .#ollama -- serve
```

The default endpoint is `http://127.0.0.1:11434`. Only one server can listen
there: quit an existing Ollama app/service before starting this command.
For automatic startup, configure a launchd service in your `nix-darwin`
configuration using the same pinned Ollama package. This flake does not install
a launchd service.

If the configured server is unavailable or older than 0.34.0, setup reports an
error rather than installing another runtime. An already running Ollama app
can still answer at the configured endpoint; changing the CLI does not replace
that server process.

Token Meter still downloads and verifies the upstream-pinned Gemma GGUF when
`token-meter-gemma` is missing, then imports it using the Nix Ollama CLI. Model
weights remain in the server's writable model store, outside the Nix store.
Work insights can still pause classification and unload its model; the server
lifecycle belongs to your external service.

## Update

```sh
nix flake update token-meter
nix build
nix flake check
```

Use Nix to update this installation rather than the upstream installer/updater.
The dashboard reports "Managed by Nix" and disables upstream update controls.
Saved update preferences cannot enable self-updating for this package.
