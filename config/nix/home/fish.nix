{
  config,
  dotfilesConfig,
  dotfilesLink,
  hermes,
  lib,
  pkgs,
  ...
}:
let
  functions = ../../.config/fish/functions;
  bindExecutables =
    lib.replaceStrings
      [
        "safe claude "
        "safe codex "
        "safe opencode "
        "safe pi "
        ''run-with-agent-env.sh" safehouse ''
        "-- hermes "
        "command hermes "
      ]
      [
        "safe ${lib.getExe pkgs.claude-code} "
        "safe ${lib.getExe pkgs.codex} "
        "safe ${lib.getExe pkgs.opencode} "
        "safe ${lib.getExe pkgs.pi-coding-agent} "
        ''run-with-agent-env.sh" ${lib.getExe pkgs.agent-safehouse} ''
        "-- ${hermes}/bin/hermes "
        "command ${hermes}/bin/hermes "
      ];
in
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
      source ${lib.escapeShellArg "${dotfilesConfig}/.config/fish/shell-init.fish"}
      fish_add_path --path --move --prepend "${config.home.profileDirectory}/bin" /run/current-system/sw/bin
    '';
    interactiveShellInit = "source ${lib.escapeShellArg "${dotfilesConfig}/.config/fish/interactive-init.fish"}";
  };

  programs.mise.enable = true;
  programs.zoxide = {
    enable = true;
    options = [
      "--cmd"
      "cd"
    ];
  };

  xdg.configFile =
    lib.mapAttrs'
      (
        name: _:
        let
          original = builtins.readFile (functions + "/${name}");
          bound = bindExecutables original;
        in
        lib.nameValuePair "fish/functions/${name}" (
          if original == bound then
            { source = dotfilesLink ".config/fish/functions/${name}"; }
          else
            { text = bound; }
        )
      )
      (
        lib.filterAttrs (name: type: type == "regular" && lib.hasSuffix ".fish" name) (
          builtins.readDir functions
        )
      )
    // {
      "mise/config.toml".source = dotfilesLink ".config/mise/config.base.toml";
      "fish/completions/wt.fish".source = dotfilesLink ".config/fish/completions/wt.fish";
      "fish/conf.d/ssh-agent.fish".source = dotfilesLink ".config/fish/conf.d/ssh-agent.fish";
    };
}
