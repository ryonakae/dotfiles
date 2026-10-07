if not set -q __fish_home_manager_config_sourced
    source "$__fish_config_dir/nix-init.fish"
end

source "$__fish_config_dir/shell-init.fish"

if status is-interactive
    source "$__fish_config_dir/interactive-init.fish"
    mise activate fish | source
    zoxide init fish --cmd cd | source
end
