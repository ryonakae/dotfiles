set -gx HOMEBREW_CASK_OPTS --appdir=/Applications
set -gx ANDROID_HOME "$HOME/Library/Android/sdk"
set -gx JAVA_HOME "/Applications/Android Studio.app/Contents/jbr/Contents/Home"
set -gx DISABLE_AUTOUPDATER 1
set -gx AGENT_BROWSER_ARGS "--no-sandbox,--disable-gpu,--disable-dev-shm-usage"
set -gx AGENT_BROWSER_PROFILE "$HOME/.config/agent-browser/profile"

fish_add_path --path --append /opt/homebrew/bin /opt/homebrew/sbin /usr/local/bin /usr/local/sbin
fish_add_path --path --append "$JAVA_HOME/bin" "$ANDROID_HOME/platform-tools"
