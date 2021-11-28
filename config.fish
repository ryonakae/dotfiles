function fish_greeting
  fish_logo
  echo ''
end

# theme
set -g theme_color_scheme dracula
set -g theme_display_date no
set -g theme_powerline_fonts no
set -g theme_nerd_fonts yes
set -g theme_display_git_master_branch yes
set -g theme_display_cmd_duration yes
set -g theme_display_user ssh
set -g theme_display_hostname ssh
set -g theme_title_display_user no
set -g theme_title_display_process yes
set -g theme_title_display_path yes

# fzf
set -U FZF_LEGACY_KEYBINDINGS 0

# homebrew
set -x HOMEBREW_CASK_OPTS --appdir=/Applications
set -U fish_user_paths "/usr/local/sbin" $fish_user_paths
# fish_add_path /opt/homebrew/bin # for Apple Silicon

# anyenv
set -x PATH $HOME/.anyenv/bin $PATH
eval (anyenv init - | source)

# direnv
eval (direnv hook fish)
set -x EDITOR Vim

# go
set -x GOPATH $HOME/go
set -x PATH $GOPATH/bin $PATH

# google-cloud sdk
set -x PATH /usr/local/Caskroom/google-cloud-sdk/latest/google-cloud-sdk/platform/google_appengine $PATH
source /usr/local/Caskroom/google-cloud-sdk/latest/google-cloud-sdk/path.fish.inc
set -x CLOUDSDK_PYTHON (which python3)

# Android SDK
set -x PATH $HOME/Library/Android/sdk/platform-tools $PATH
set -x ANDROID_SDK $HOME/Library/Android/sdk

# PostgreSQL
set -x PGDATA /usr/local/var/postgres
