function fish_greeting
  fish_logo

  set_color $fish_color_autosuggestion
  uname -nmsr
  command -s uptime >/dev/null
  and uptime
  set_color normal
end

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

# homebrew
set -x HOMEBREW_CASK_OPTS --appdir=/Applications
set -g fish_user_paths "/usr/local/sbin" $fish_user_paths

# *env
status --is-interactive; and source (nodenv init -|psub)
status --is-interactive; and source (rbenv init -|psub)
status --is-interactive; and source (pyenv init -|psub)
status --is-interactive; and source (goenv init -|psub)

# direnv
set -x EDITOR Vim

# openssl
set -x PATH /usr/local/opt/openssl/bin $PATH
set -x LDFLAGS -L/usr/local/opt/openssl/lib
set -x CPPFLAGS -I/usr/local/opt/openssl/include
set -x PKG_CONFIG_PATH /usr/local/opt/openssl/lib/pkgconfig

# go
set -Ux GOPATH $HOME/go
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
