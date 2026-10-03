{ pkgs }:
pkgs.stdenvNoCC.mkDerivation (final: {
  pname = "opencode";
  version = "1.18.33";
  src = pkgs.fetchurl {
    url = "https://github.com/anomalyco/opencode/releases/download/v${final.version}/opencode-darwin-arm64.zip";
    hash = "sha256-JLEoc+YFs9szh8s1X0O6dFHNYGXBgNjBiGYzN9LutVM=";
  };
  nativeBuildInputs = [
    pkgs.unzip
    pkgs.makeBinaryWrapper
  ];
  sourceRoot = ".";
  dontBuild = true;
  # The upstream executable is already signed.
  dontFixup = true;
  installPhase = ''
    runHook preInstall
    install -Dm755 opencode "$out/bin/opencode"
    wrapProgram "$out/bin/opencode" \
      --set OPENCODE_DISABLE_AUTOUPDATE true \
      --prefix PATH : ${
        pkgs.lib.makeBinPath [
          pkgs.ripgrep
          pkgs.sysctl
        ]
      }
    runHook postInstall
  '';
  meta = {
    inherit (pkgs.opencode.meta)
      description
      homepage
      license
      mainProgram
      ;
    platforms = [ "aarch64-darwin" ];
    sourceProvenance = [ pkgs.lib.sourceTypes.binaryNativeCode ];
  };
})
