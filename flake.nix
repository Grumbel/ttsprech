{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-22.05";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachSystem [ "i686-linux" "x86_64-linux" ] (system:
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
            doCheck = false;
            checkPhase = ''
              runHook preCheck
              flake8
              pyright ttsprech
              mypy -p ttsprech
              pylint ttsprech
              python -m unittest discover
              runHook postCheck
            '';
            checkInputs = (with pkgs; [
              pyright
            ]) ++ (with pythonPackages; [
              mypy
              flake8
              pylint
            ]);
            nativeBuildInputs = with pythonPackages; [
              setuptools
            ];
            propagatedBuildInputs = with pythonPackages; [
              langdetect
              nltk
              num2words
              pyxdg
              simpleaudio
            ] ++ [
              pkgs.tts
            ];
          };

          ttsprech-check = ttsprech.override {
            doCheck = true;
          };

          default = ttsprech;
        };

        apps = rec {
          ttsprech = flake-utils.lib.mkApp {
            drv = packages.ttsprech;
          };
          default = ttsprech;
        };

        devShells = rec {
          ttsprech = pkgs.mkShell {
            inputsFrom = [ packages.ttsprech-check ];
          };
          default = ttsprech;
        };
      }
    );
}
