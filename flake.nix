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
        pkgs = nixpkgs.legacyPackages.${system};
        pythonPackages = pkgs.python3Packages;
      in rec {
        packages = flake-utils.lib.flattenTree rec {
          nltk_data_punkt = pkgs.fetchzip {
            url = "https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/tokenizers/punkt.zip";
            hash = "sha256-zAbLxd0h/XYrLSSxevEHLsOAydT3VHnRO7QW2Q7abIQ=";
          };

          ttsprech = pythonPackages.buildPythonPackage rec {
            pname = "ttsprech";
            version = "0.0.0";
            src = ./.;
            patchPhase = ''
              substituteInPlace ttsprech/ttsprech.py --replace \
                "NLTK_DATA_PUNKT_DIR_PLACEHOLDER" "${nltk_data_punkt}"
            '';
            checkPhase = ''
              runHook preCheck
              mypy -p ttsprech
              flake8
              pylint ttsprech
              python -m unittest discover
              runHook postCheck
            '';
            checkInputs =  with pythonPackages; [
              mypy
              flake8
              pylint
            ];
            nativeBuildInputs = with pythonPackages; [
              setuptools
            ];
            propagatedBuildInputs = with pythonPackages; [
              langdetect
              nltk
              num2words
              pyxdg
              simpleaudio
              torchaudio-bin
            ];
          };
        };
        defaultPackage = packages.ttsprech;
        devShell = pkgs.mkShell {
          inputsFrom = [ defaultPackage ];
        };
      }
    );
}
