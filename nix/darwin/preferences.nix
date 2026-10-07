{ config, ... }:
let
  homeDirectory = config.users.users.${config.system.primaryUser}.home;
in
{
  system.defaults = {
    NSGlobalDomain = {
      AppleShowAllExtensions = true;
      AppleInterfaceStyleSwitchesAutomatically = true;
      AppleKeyboardUIMode = 2;
      AppleShowScrollBars = "WhenScrolling";
      "com.apple.keyboard.fnState" = true;
      _HIHideMenuBar = false;
      InitialKeyRepeat = 15;
      KeyRepeat = 2;
      NSAutomaticCapitalizationEnabled = false;
      NSAutomaticPeriodSubstitutionEnabled = false;
      NSAutomaticSpellingCorrectionEnabled = false;
    };
    dock = {
      autohide = true;
      autohide-delay = 0.0;
      autohide-time-modifier = 0.15;
      tilesize = 64;
      show-recents = false;
      mru-spaces = false;
      expose-group-apps = true;
      wvous-tl-corner = 2;
      wvous-tr-corner = 12;
      wvous-bl-corner = 3;
      wvous-br-corner = 4;
      persistent-apps = [
        "/Applications/Spark Desktop.app"
        "/Applications/1Password.app"
        "/Applications/CleanArchiver.app"
        "/Applications/Google Chrome.app"
        "/Applications/Slack.app"
        "/Applications/Notion Calendar.app"
        "/Applications/Bear.app"
        "/Applications/CotEditor.app"
        "/Applications/Figma.app"
        "/Applications/Figma Beta.app"
        "/Applications/Ghostty.app"
        "/Applications/Zed.app"
        "${homeDirectory}/Applications/Chrome Apps.localized/X.app"
        "${homeDirectory}/Applications/Chrome Apps.localized/Bluesky.app"
        "/Applications/Spotify.app"
        "/Applications/LINE.app"
      ];
      persistent-others = [
        {
          folder = {
            path = "/Applications";
            arrangement = "name";
            displayas = "folder";
            showas = "automatic";
          };
        }
        {
          folder = {
            path = "${homeDirectory}/Downloads";
            arrangement = "date-added";
            displayas = "folder";
            showas = "fan";
          };
        }
      ];
    };
    finder = {
      ShowPathbar = true;
      ShowStatusBar = true;
      FXPreferredViewStyle = "Nlsv";
      FXDefaultSearchScope = "SCcf";
      NewWindowTarget = "Home";
      ShowHardDrivesOnDesktop = false;
      ShowExternalHardDrivesOnDesktop = false;
      ShowRemovableMediaOnDesktop = true;
      _FXSortFoldersFirst = true;
    };
    screencapture.show-thumbnail = true;
    menuExtraClock = {
      ShowDate = 0;
      ShowDayOfWeek = true;
    };
    controlcenter = {
      BatteryShowPercentage = true;
      Sound = true;
    };
    WindowManager.GloballyEnabled = false;
    CustomUserPreferences = {
      NSGlobalDomain.WebAutomaticSpellingCorrectionEnabled = false;
      "com.apple.dock" = {
        wvous-tl-modifier = 0;
        wvous-tr-modifier = 0;
        wvous-bl-modifier = 0;
        wvous-br-modifier = 0;
      };
    };
    trackpad = {
      Clicking = false;
      TrackpadThreeFingerDrag = false;
    };
  };
}
