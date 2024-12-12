{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs?ref=nixos-24.11";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachSystem [ "i686-linux" "x86_64-linux" ] (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        pythonPackages = pkgs.python3Packages;
      in rec {
        packages = rec {
          default = ttsprech;

          nltk_data_punkt = pkgs.fetchzip {
            url = "https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/tokenizers/punkt.zip";
            hash = "sha256-SKZu26K17qMUg7iCFZey0GTECUZ+sTTrF/pqeEgJCos=";
          };

          nltk_data_punkt_tab = pkgs.fetchzip {
            url = "https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/tokenizers/punkt_tab.zip";
            hash = "sha256-kZmznOzjZt9CMcHdf+hZZ4fst6rczzdaQMNlak4rrio=";
          };

          silero-model-v3_en = pkgs.fetchurl {
            url = "https://models.silero.ai/models/tts/en/v3_en.pt";
            hash = "sha256-ArcQNNnxO8QAEZUBe6ydsca7YRXgP+pSmD6KvP8TtmU=";
          };

          ttsprech = pythonPackages.buildPythonPackage rec {
            pname = "ttsprech";
            version = "0.0.0";

            src = ./.;

            patchPhase = ''
              substituteInPlace ttsprech/ttsprech.py \
                --replace "NLTK_DATA_DIRS_PLACEHOLDER" "${nltk_data_punkt}:${nltk_data_punkt_tab}" \
                --replace "SILERO_MODEL_FILE_PLACEHOLDER" "${silero-model-v3_en}"
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
        };

        apps = rec {
          default = ttsprech;
          ttsprech = flake-utils.lib.mkApp {
            drv = packages.ttsprech;
          };
        };

        devShells = rec {
          default = ttsprech;
          ttsprech = pkgs.mkShell {
            inputsFrom = [ packages.ttsprech-check ];
          };
        };
      }
    );
}
