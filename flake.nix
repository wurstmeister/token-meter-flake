{
  description = "Token Meter — local usage and cost dashboard for AI coding agents";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    token-meter = {
      url = "github:splunk/token-meter";
      flake = false;
    };
  };

  outputs = { nixpkgs, token-meter, ... }:
    let
      systems = [ "aarch64-darwin" "x86_64-darwin" "aarch64-linux" "x86_64-linux" ];
      forAllSystems = nixpkgs.lib.genAttrs systems;
      mkPackage = pkgs: pkgs.stdenvNoCC.mkDerivation {
        pname = "token-meter";
        version = "0-unstable-${token-meter.shortRev}";
        src = token-meter;

        nativeBuildInputs = [ pkgs.makeWrapper ];
        patches = [ ./nix-ollama.patch ./nix-updates.patch ];
        patchFlags = [ "-p1" "--no-backup-if-mismatch" ];
        postPatch = ''
          substituteInPlace token_meter/services/work_setup.py \
            --replace-fail '@nixOllama@' '${pkgs.ollama}' \
            --replace-fail 'OLLAMA_VERSION = "0.34.4"' 'OLLAMA_VERSION = "${pkgs.ollama.version}"'
        '';
        dontBuild = true;

        installPhase = ''
          runHook preInstall
          mkdir -p "$out/share/token-meter" "$out/bin"
          cp -r meter.py token_meter token_meter_mcp.py page.html performance.html \
            runtime-manifest.txt assets menubar scripts LICENSE "$out/share/token-meter/"
          makeWrapper ${pkgs.python3}/bin/python3 "$out/bin/token-meter" \
            --add-flags "$out/share/token-meter/meter.py" \
            --set PYTHONDONTWRITEBYTECODE 1 \
            --prefix PATH : ${pkgs.lib.makeBinPath [ pkgs.git ]}
          makeWrapper ${pkgs.python3}/bin/python3 "$out/bin/token-meter-mcp" \
            --add-flags "$out/share/token-meter/token_meter_mcp.py" \
            --set PYTHONDONTWRITEBYTECODE 1
          cp "$out/bin/token-meter-mcp" "$out/share/token-meter/scripts/run-token-meter-mcp"
          runHook postInstall
        '';

        meta = {
          description = "Local-first usage and cost dashboard for AI coding agents";
          homepage = "https://github.com/splunk/token-meter";
          license = pkgs.lib.licenses.mit;
          platforms = systems;
          mainProgram = "token-meter";
        };
      };
    in {
      packages = forAllSystems (system:
        let package = mkPackage nixpkgs.legacyPackages.${system};
        in {
          default = package;
          token-meter = package;
          ollama = nixpkgs.legacyPackages.${system}.ollama;
        });

      apps = forAllSystems (system: {
        ollama = {
          type = "app";
          program = "${nixpkgs.legacyPackages.${system}.ollama}/bin/ollama";
        };
        default = {
          type = "app";
          program = "${mkPackage nixpkgs.legacyPackages.${system}}/bin/token-meter";
        };
        mcp = {
          type = "app";
          program = "${mkPackage nixpkgs.legacyPackages.${system}}/bin/token-meter-mcp";
        };
      });

      checks = forAllSystems (system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          package = mkPackage pkgs;
        in {
          runtime = pkgs.runCommand "token-meter-runtime-check" { } ''
            export HOME="$TMPDIR/home"
            mkdir -p "$HOME"
            export PYTHONDONTWRITEBYTECODE=1
            cd ${package}/share/token-meter
            export PYTHONPATH="$PWD"
            ${pkgs.python3}/bin/python3 -c 'import meter; import token_meter_mcp; assert meter.PORT == 8722'
            ${pkgs.python3}/bin/python3 ${./test_work_setup.py}
            ${pkgs.python3}/bin/python3 ${./test_packaging.py}
            test -s page.html
            test -s performance.html
            touch "$out"
          '';
        });
    };
}
