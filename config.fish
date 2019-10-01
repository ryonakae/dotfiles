# theme
set -g theme_display_date no
set -g theme_powerline_fonts no
set -g theme_nerd_fonts yes
set -g theme_display_git_master_branch yes
set -g theme_display_cmd_duration yes
set -g theme_color_scheme dracula
set -g theme_display_user ssh
set -g theme_display_hostname ssh

# fzf
set -U FZF_LEGACY_KEYBINDINGS 0

# env
status --is-interactive; and source (nodenv init -|psub)
status --is-interactive; and source (rbenv init -|psub)
status --is-interactive; and source (pyenv init -|psub)
status --is-interactive; and source (goenv init -|psub)

# go
set -Ux GOPATH $HOME/go
set -x PATH $GOPATH/bin $PATH

# google-cloud sdk
set -x PATH /usr/local/Caskroom/google-cloud-sdk/latest/google-cloud-sdk/platform/google_appengine $PATH
source /usr/local/Caskroom/google-cloud-sdk/latest/google-cloud-sdk/path.fish.inc
