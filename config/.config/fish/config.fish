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

for plugin in bobthefish fzf
    set -l plugin_dir "$__fish_config_dir/plugins/$plugin"
    if test -d "$plugin_dir/functions"
        set fish_function_path $fish_function_path[1] "$plugin_dir/functions" $fish_function_path[2..-1]
    end
    if test -d "$plugin_dir/completions"
        set fish_complete_path $fish_complete_path[1] "$plugin_dir/completions" $fish_complete_path[2..-1]
    end
end

if status is-interactive
    function fish_greeting
        echo ""
    end

    set -g fish_color_command blue
    set -g fish_color_autosuggestion brblack
    set -g fish_color_cancel -r
    set -g fish_color_comment red
    set -g fish_color_cwd green
    set -g fish_color_cwd_root red
    set -g fish_color_end green
    set -g fish_color_error brred
    set -g fish_color_escape brcyan
    set -g fish_color_history_current --bold
    set -g fish_color_host normal
    set -g fish_color_host_remote yellow
    set -g fish_color_normal normal
    set -g fish_color_operator brcyan
    set -g fish_color_param cyan
    set -g fish_color_quote yellow
    set -g fish_color_redirection cyan --bold
    set -g fish_color_search_match white --background=brblack
    set -g fish_color_selection white --bold --background=brblack
    set -g fish_color_status red
    set -g fish_color_user brgreen
    set -g fish_color_valid_path --underline

    set -g fish_pager_color_completion normal
    set -g fish_pager_color_description yellow -i
    set -g fish_pager_color_prefix normal --bold --underline
    set -g fish_pager_color_progress brwhite --background=cyan
    set -g fish_pager_color_selected_background -r

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

    for plugin in bobthefish fzf
        for init in "$__fish_config_dir/plugins/$plugin"/conf.d/*.fish
            source "$init"
        end
    end

    command mise activate fish | source
    zoxide init fish --cmd cd | source
end
