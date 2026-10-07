{ config, pkgs, ... }:
{
  programs.fish = {
    enable = true;
    plugins = [
      {
        name = "bobthefish";
        src = pkgs.fishPlugins.bobthefish.src;
      }
      {
        name = "fzf";
        src = pkgs.fishPlugins.fzf.src;
      }
    ];
    shellInit = ''
      fish_add_path --path --move --prepend "${config.home.profileDirectory}/bin" /run/current-system/sw/bin
    '';
  };

  # Keep Nix integration without owning the editable shell entrypoint.
  xdg.configFile."fish/config.fish".target = "${config.xdg.configHome}/fish/nix-init.fish";
  programs.mise = {
    enable = true;
    enableFishIntegration = false;
  };
}
