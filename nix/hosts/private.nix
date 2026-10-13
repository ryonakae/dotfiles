{
  power = {
    restartAfterPowerFailure = true;
    sleep = {
      computer = "never";
      display = 20;
      harddisk = "never";
      allowSleepByPowerButton = false;
    };
  };

  system.defaults = {
    CustomUserPreferences."com.apple.screensaver".idleTime = 600;
    screensaver = {
      askForPassword = true;
      askForPasswordDelay = 0;
    };
  };

  homebrew = {
    brews = [
      "rtk"
    ];

    casks = [
      "air-video-server-hd"
      "autodesk-fusion"
      "eagle"
      "freecad"
      "kicad"
      "parallels"
      "private-internet-access"
      "qmk-toolbox"
      "timemachineeditor"
    ];

    masApps = {
      "EdgeView 2" = 1206246482;
    };
  };
}
