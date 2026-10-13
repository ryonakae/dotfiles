if not set -q __fish_home_manager_config_sourced
    source "$__fish_config_dir/nix-init.fish"
end

set -gx HOMEBREW_CASK_OPTS --appdir=/Applications
set -gx ANDROID_HOME "$HOME/Library/Android/sdk"
set -gx JAVA_HOME "/Applications/Android Studio.app/Contents/jbr/Contents/Home"
set -gx DISABLE_AUTOUPDATER 1
set -gx AGENT_BROWSER_ARGS "--no-sandbox,--disable-gpu,--disable-dev-shm-usage"
set -gx AGENT_BROWSER_PROFILE "$HOME/.config/agent-browser/profile"

set -l mise_data_dir "$HOME/.local/share/mise"
if set -q MISE_DATA_DIR; and test -n "$MISE_DATA_DIR"
    set mise_data_dir "$MISE_DATA_DIR"
end
fish_add_path --path --move --prepend "$HOME/.local/bin" "$mise_data_dir/shims"
fish_add_path --path --append /opt/homebrew/bin /opt/homebrew/sbin /usr/local/bin /usr/local/sbin
fish_add_path --path --append "$JAVA_HOME/bin" "$ANDROID_HOME/platform-tools"

if status is-interactive
    function fish_greeting
        echo ""
    end

    set -g fish_color_command blue
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

    mise activate fish | source
    zoxide init fish --cmd cd | source
end
