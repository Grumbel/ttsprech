{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-22.05";
    flake-utils.url = "github:numtide/flake-utils";

    silero-src.url = "github:snakers4/silero-models?ref=v0.4.1";
    silero-src.flake = false;
  };

  outputs = { self, nixpkgs, flake-utils, silero-src }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          config = { allowUnfree = true; };
        };
      in rec {
        packages = flake-utils.lib.flattenTree rec {
          silero = pkgs.python3Packages.buildPythonPackage rec {
            pname = "silero";
            version = "0.4.1";
            src = silero-src;
            patchPhase = ''
            cat > setup.py <<EOF
            from setuptools import setup
            setup(use_scm_version=True)
            EOF
            '';
            nativeBuildInputs = with pkgs; [
              python3Packages.setuptools
            ];
            propagatedBuildInputs = with pkgs; [
              #python3Packages.pytorch
              python3Packages.torchaudio-bin
              python3Packages.omegaconf
            ];
          };

          silero-test = pkgs.python3Packages.buildPythonPackage rec {
            pname = "silero-test";
            version = "0.0.0";
            src = ./.;
            propagatedBuildInputs = with pkgs; [
              silero
              python3Packages.pyxdg
            ];
          };
        };
        defaultPackage = packages.silero-test;
      }
    );
}
