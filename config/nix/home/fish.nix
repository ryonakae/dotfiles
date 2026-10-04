{
  config,
  inputs,
  lib,
  pkgs,
  ...
}:
let
  functions = ../../.config/fish/functions;
  hermes = inputs.hermes-agent.packages.${pkgs.stdenv.hostPlatform.system}.default;
  bindExecutables =
    lib.replaceStrings
      [
        "safe claude "
        "safe codex "
        "safe opencode "
        "safe pi "
        ''run-with-agent-env.sh" safehouse ''
        "-- hermes "
      ]
      [
        "safe ${lib.getExe pkgs.claude-code} "
        "safe ${lib.getExe pkgs.codex} "
        "safe ${lib.getExe pkgs.opencode} "
        "safe ${lib.getExe pkgs.pi-coding-agent} "
        ''run-with-agent-env.sh" ${lib.getExe pkgs.agent-safehouse} ''
        "-- ${hermes}/bin/hermes "
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
      source ${../../.config/fish/shell-init.fish}
      fish_add_path --path --move --prepend "${config.home.profileDirectory}/bin" /run/current-system/sw/bin
    '';
    interactiveShellInit = "source ${../../.config/fish/interactive-init.fish}";
    shellInitLast = "__dotfiles_keep_rm_first";
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
        lib.nameValuePair "fish/functions/${name}" {
          text = bindExecutables (builtins.readFile (functions + "/${name}"));
        }
      )
      (
        lib.filterAttrs (name: type: type == "regular" && lib.hasSuffix ".fish" name) (
          builtins.readDir functions
        )
      )
    // {
      "mise/config.toml".source = ../../.config/mise/config.base.toml;
      "fish/completions/wt.fish".source = ../../.config/fish/completions/wt.fish;
      "fish/conf.d/ssh-agent.fish".source = ../../.config/fish/conf.d/ssh-agent.fish;
      "fish/conf.d/gomi.fish".source = ../../.config/fish/conf.d/gomi.fish;
    };
}
