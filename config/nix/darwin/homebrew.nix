{ machine, ... }:
{
  nix-homebrew = {
    enable = true;
    user = machine.username;
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
    taps = [ "ryonakae/tap" ];

    brews = [
      # The firewall helper signs the installed binary in place.
      "mosh"
      "ryonakae/tap/zerdr"
    ];

    casks = [
      "1password"
      "1password-cli"
      "adobe-creative-cloud"
      "affinity"
      "android-studio"
      "appcleaner"
      "bettertouchtool"
      "chatgpt"
      "claude"
      "cleanshot"
      "cmd-eikana"
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
    ];

    # CotEditor currently has an App Store receipt; do not also install its cask.
    masApps = {
      Barbee = 1548711022;
      Bear = 1091189122;
      CotEditor = 1024640650;
      "Disk Diag" = 672206759;
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
      Perplexity = 6714467650;
      Transmit = 403388562;
      Transporter = 1450874784;
      Velja = 1607635845;
      Xcode = 497799835;
    };
  };
}
