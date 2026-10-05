{
  config,
  dotfilesLink,
  lib,
  pkgs,
  ...
}:
{
  home.sessionPath = [ "${config.home.homeDirectory}/.local/bin" ];
  xdg.configFile = {
    "gomi/config.yaml".source = dotfilesLink ".config/gomi/config.yaml";
    "agent-safehouse/compatibility.sb".source = dotfilesLink ".config/agent-safehouse/compatibility.sb";
    "agent-safehouse/local-overrides.sb".source =
      dotfilesLink ".config/agent-safehouse/local-overrides.sb";
    "agent-safehouse/run-with-agent-env.sh" = {
      text = lib.replaceStrings [ "exec dotenvx " ] [ "exec ${lib.getExe pkgs.dotenvx} " ] (
        builtins.readFile ../../.config/agent-safehouse/run-with-agent-env.sh
      );
      executable = true;
    };
  };
}
