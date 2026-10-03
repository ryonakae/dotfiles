{ pkgs }:
pkgs.stdenvNoCC.mkDerivation (final: {
  pname = "codex";
  version = "0.159.1";
  src = pkgs.fetchurl {
    url = "https://github.com/openai/codex/releases/download/rust-v${final.version}/codex-package-aarch64-apple-darwin.tar.gz";
    hash = "sha256-qPx2zLUjDdl/ttsBhz+pwSteHv3zLRPCun9uhInM2JM=";
  };
  sourceRoot = ".";
  dontBuild = true;
  # Preserve upstream signatures and relative paths to companion executables.
  dontFixup = true;
  installPhase = ''
    runHook preInstall
    mkdir -p "$out"
    cp -R bin codex-path codex-resources codex-package.json "$out/"
    runHook postInstall
  '';
  meta = {
    inherit (pkgs.codex.meta)
      description
      homepage
      license
      mainProgram
      ;
    platforms = [ "aarch64-darwin" ];
    sourceProvenance = [ pkgs.lib.sourceTypes.binaryNativeCode ];
  };
})
