{ pkgs }:
pkgs.claude-code.overrideAttrs (
  final: _: {
    version = "2.1.285";
    src = pkgs.fetchurl {
      url = "https://downloads.claude.ai/claude-code-releases/${final.version}/darwin-arm64/claude.zst";
      sha256 = "37ef7ca4ef6486c44b8f88b41af4f269ba8322c7dd8a62261e54e3271f56a6a0";
    };
  }
)
