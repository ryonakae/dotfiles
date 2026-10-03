{ config, pkgs, ... }:
{
  home.sessionPath = [ "${config.home.homeDirectory}/.local/bin" ];
  home.file.".local/bin/rm" = {
    executable = true;
    text =
      builtins.replaceStrings
        [ "#!/usr/bin/env -S uv run --no-project --script" ]
        [ "#!${pkgs.python311}/bin/python3" ]
        (builtins.readFile ../../.local/bin/rm);
  };

  xdg.configFile = {
    "gomi/config.yaml".source = ../../.config/gomi/config.yaml;
    "agent-safehouse/compatibility.sb".source = ../../.config/agent-safehouse/compatibility.sb;
    "agent-safehouse/local-overrides.sb".source = ../../.config/agent-safehouse/local-overrides.sb;
    "agent-safehouse/run-with-agent-env.sh" = {
      source = ../../.config/agent-safehouse/run-with-agent-env.sh;
      executable = true;
    };
  };
}
