{ pkgs }:
pkgs.pi-coding-agent.overrideAttrs (
  final: previous: {
    version = "1.0.0";
    src = pkgs.fetchFromGitHub {
      owner = "earendil-works";
      repo = "pi";
      tag = "v${final.version}";
      hash = "sha256-CGznIVHXG6gr2F8vzHcR/v4P9xJgZHeMTt/CJ/kB78o=";
    };
    npmDepsHash = "sha256-ndEvWdB6sa5nNNtabk2OMZKUFG9x3op185deZHxFnXk=";
    # The inherited npmDeps derivation otherwise retains the original source.
    npmDeps = previous.npmDeps.overrideAttrs {
      inherit (final) src;
      name = "pi-coding-agent-${final.version}-npm-deps";
      outputHash = final.npmDepsHash;
    };
    modelData = pkgs.fetchurl {
      url = "https://registry.npmjs.org/@earendil-works/pi-ai/-/pi-ai-${final.version}.tgz";
      hash = "sha256-85uZwpuFmPF1sQhA5dKoGYPnwM5crk19+DoQB0R9LCs=";
    };
  }
)
