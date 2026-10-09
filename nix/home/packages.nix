{ hermes, pkgs, ... }:
{
  home.packages = [
    hermes
    pkgs.nixd
  ];
}
