{
  config,
  lib,
  pkgs,
  ...
}:
let
  functions = ../../.config/fish/functions;
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
      set -gx HOMEBREW_CASK_OPTS --appdir=/Applications
      set -gx ANDROID_HOME "$HOME/Library/Android/sdk"
      set -gx JAVA_HOME "/Applications/Android Studio.app/Contents/jbr/Contents/Home"
      set -gx DISABLE_AUTOUPDATER 1
      set -gx AGENT_BROWSER_ARGS "--no-sandbox,--disable-gpu,--disable-dev-shm-usage"
      set -gx AGENT_BROWSER_PROFILE "$HOME/.config/agent-browser/profile"

      fish_add_path --path --append /opt/homebrew/bin /opt/homebrew/sbin /usr/local/bin /usr/local/sbin
      fish_add_path --path --append "$JAVA_HOME/bin" "$ANDROID_HOME/platform-tools"
      fish_add_path --path --move --prepend "${config.home.profileDirectory}/bin" /run/current-system/sw/bin
    '';

    interactiveShellInit = ''
      function fish_greeting
        echo ""
      end
      set -g theme_color_scheme dracula
      set -g theme_display_date no
      set -g theme_display_cmd_duration yes
      set -g theme_powerline_fonts no
      set -g theme_nerd_fonts yes
      set -g theme_display_git_master_branch yes
      set -g theme_display_user ssh
      set -g theme_display_hostname ssh
      set -g theme_title_display_user no
      set -g theme_title_display_process yes
      set -g theme_title_display_path yes
      set -g FZF_LEGACY_KEYBINDINGS 0
    '';

    # mise can prepend project runtimes after shell initialization.
    functions.__dotfiles_keep_rm_first = {
      onVariable = "PATH";
      body = ''
        if test "$PATH[1]" != "$HOME/.local/bin"
          fish_add_path --path --move --prepend "$HOME/.local/bin"
        end
      '';
    };
    shellInitLast = "__dotfiles_keep_rm_first";
  };

  programs.mise = {
    enable = true;
    globalConfig.settings = {
      idiomatic_version_file_enable_tools = [ ];
      ruby.compile = true;
    };
  };
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
          source = functions + "/${name}";
        }
      )
      (
        lib.filterAttrs (name: type: type == "regular" && lib.hasSuffix ".fish" name) (
          builtins.readDir functions
        )
      )
    // {
      "fish/completions/wt.fish".source = ../../.config/fish/completions/wt.fish;
      "fish/conf.d/ssh-agent.fish".source = ../../.config/fish/conf.d/ssh-agent.fish;
      "fish/conf.d/gomi.fish".source = ../../.config/fish/conf.d/gomi.fish;
    };
}
