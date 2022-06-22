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

          nltk_data_punkt = pkgs.fetchzip {
            url = "https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/tokenizers/punkt.zip";
            hash = "sha256-zAbLxd0h/XYrLSSxevEHLsOAydT3VHnRO7QW2Q7abIQ=";
          };

          ttsprech = pkgs.python3Packages.buildPythonPackage rec {
            pname = "ttsprech";
            version = "0.0.0";
            src = ./.;
            patchPhase = ''
              substituteInPlace ttsprech/ttsprech.py --replace \
                "NLTK_DATA_PUNKT_DIR_PLACEHOLDER" "${nltk_data_punkt}"
            '';
            checkPhase = ''
              runHook preCheck
              ${pkgs.python3Packages.mypy}/bin/mypy -p ttsprech
              ${pkgs.python3Packages.python.interpreter} -m unittest discover
              runHook postCheck
            '';
            nativeBuildInputs = with pkgs; [
              python3Packages.setuptools
              python3Packages.flake8
              python3Packages.mypy
            ];
            propagatedBuildInputs = with pkgs; [
              silero
              python3Packages.nltk
              python3Packages.langdetect
              python3Packages.pyxdg
              python3Packages.simpleaudio
            ];
          };
        };
        defaultPackage = packages.ttsprech;
      }
    );
}
