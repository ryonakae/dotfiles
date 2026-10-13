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

  homebrew = {
    brews = [
      "rtk"
    ];

    casks = [
      "air-video-server-hd"
      "private-internet-access"
      "timemachineeditor"
    ];

    masApps = {
      "EdgeView 2" = 1206246482;
    };
  };
}
