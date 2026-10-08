{ config, ... }:
{
  nix-homebrew = {
    enable = true;
    user = config.system.primaryUser;
    autoMigrate = true;
  };

  homebrew = {
    enable = true;
    onActivation = {
      autoUpdate = false;
      upgrade = false;
      cleanup = "none";
    };
    caskArgs.appdir = "/Applications";
    taps = [
      "ryonakae/tap"
      "eugene1g/safehouse"
      "dotenvx/brew"
      "trasta298/tap"
    ];

    brews = [
      "actionlint"
      "age"
      "agent-browser"
      "eugene1g/safehouse/agent-safehouse"
      "cocoapods"
      "ctx7"
      "dotenvx/brew/dotenvx"
      "exiftool"
      "fastlane"
      "fd"
      "ffmpeg"
      "fzf"
      "gh"
      "git"
      "git-lfs"
      "gomi"
      "googleworkspace-cli"
      "herdr"
      "imagemagick"
      "jq"
      "trasta298/tap/keifu"
      "mas"
      "mkcert"
      "mole"
      # The firewall helper signs the installed binary in place.
      "mosh"
      "opencode"
      "pi-coding-agent"
      "qrencode"
      "ripgrep"
      "terminal-notifier"
      "tmux"
      "tree"
      "uv"
      "vim"
      "worktrunk"
      "yazi"
      "ryonakae/tap/zerdr"
      "zoxide"
    ];

    casks = [
      "1password"
      "1password-cli"
      "adobe-creative-cloud"
      "affinity"
      "android-studio"
      "antigravity-cli"
      "appcleaner"
      "bettertouchtool"
      "chatgpt"
      "claude"
      "claude-code@latest"
      "cleanshot"
      "cmd-eikana"
      "codex"
      "contexts"
      "cursor"
      "cursorsense"
      "discord"
      "docker-desktop"
      "dropbox"
      "figma"
      "figma@beta"
      "font-hackgen-nerd"
      "font-sauce-code-pro-nerd-font"
      "font-sf-mono"
      "font-sf-pro"
      "font-source-han-code-jp"
      "gcloud-cli"
      "ghostty"
      "google-chrome"
      "google-drive"
      "google-japanese-ime@dev"
      "imageoptim"
      "karabiner-elements"
      "keepingyouawake"
      "logi-options+"
      "monitorcontrol"
      "monocle-app"
      "notion-calendar"
      "obs"
      "ogdesign-eagle"
      "raycast"
      "readdle-spark"
      "rectangle"
      "ryonakae/tap/sheltie"
      "sf-symbols"
      "slack"
      "smoothcsv"
      "sourcetree"
      "spotify"
      "tailscale-app"
      "the-unarchiver"
      "typeface"
      "unity-cli"
      "unity-hub"
      "via"
      "visual-studio-code"
      "visual-studio-code@insiders"
      "vlc"
      "zed"
      "zoom"
    ];

    # CotEditor currently has an App Store receipt; do not also install its cask.
    masApps = {
      Barbee = 1548711022;
      Bear = 1091189122;
      CotEditor = 1024640650;
      "Ethernet Menubar" = 1549412235;
      GarageBand = 682658836;
      iMovie = 408981434;
      Keynote = 409183694;
      LINE = 539883307;
      "Microsoft Excel" = 462058435;
      "Microsoft OneNote" = 784801555;
      "Microsoft Outlook" = 985367838;
      "Microsoft PowerPoint" = 462062816;
      "Microsoft Word" = 462054704;
      Numbers = 409203825;
      "Okta Extension App" = 1439967473;
      Pages = 409201541;
      Transmit = 403388562;
      Transporter = 1450874784;
      "Unsplash Wallpapers" = 1284863847;
      Velja = 1607635845;
      Xcode = 497799835;
    };
  };
}
