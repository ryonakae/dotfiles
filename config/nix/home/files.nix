{ pkgs, ... }:
{
  xdg.configFile = {
    "yazi/plugins/git.yazi".source = pkgs.yaziPlugins.git;
    "yazi/plugins/smart-enter.yazi".source = pkgs.yaziPlugins.smart-enter;
    "yazi/plugins/full-border.yazi".source = pkgs.yaziPlugins.full-border;
  };
}
