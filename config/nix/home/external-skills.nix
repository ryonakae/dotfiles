{ pkgs }:
let
  techWriting = pkgs.fetchFromGitHub {
    owner = "f4ah6o";
    repo = "tech-write-ja";
    rev = "244f573d90b593e3f227879302ad96fd154a4ee3";
    hash = "sha256-Jyc+hkpup9yEhkaw2vo8b2MDwjLYJxnAa/9IERqZ7bo=";
  };
in
{
  agent-browser =
    (pkgs.fetchFromGitHub {
      owner = "vercel-labs";
      repo = "agent-browser";
      rev = "526157cfd4ec64f45939f9ba0f10d5936aa7ac33";
      hash = "sha256-LReBma9Mrr/HyunQ4FlcdZS0CTZZ8qKZjrPqyLTP9hY=";
    })
    + "/skills/agent-browser";
  agent-device =
    (pkgs.fetchFromGitHub {
      owner = "callstack";
      repo = "agent-device";
      rev = "be3c8104ddc2980f6b1200968d302c20063c8887";
      hash = "sha256-BoYefyJ8znVWNAg15Ea3XGiYIokXmYLDZTaX5x8505A=";
    })
    + "/skills/agent-device";
  cognitive-rhythm-writing = techWriting + "/skills/cognitive-rhythm-writing";
  find-docs =
    (pkgs.fetchFromGitHub {
      owner = "upstash";
      repo = "context7";
      rev = "bfa02ea67b5707fe0e0a673faa49d0f50b28c80b";
      hash = "sha256-5gckAd+rfGafB9KZPCS1jJqXjA2vF0VXoGHJngDFtUQ=";
    })
    + "/skills/find-docs";
  herdr =
    (pkgs.fetchFromGitHub {
      owner = "herdrdev";
      repo = "herdr";
      rev = "cee4fc2dc6ef2b9269636fc5dc876ecb44ee039f";
      hash = "sha256-MAWXZWpOPR9EXCZ+9oNb2PoT0U2ExcW9AgKeGJOQRdc=";
    })
    + "/skills/herdr";
  japanese-tech-writing = techWriting + "/skills/japanese-tech-writing";
  readme-creator =
    (pkgs.fetchFromGitHub {
      owner = "mblode";
      repo = "agent-skills";
      rev = "24f4fd8bdbb7ef6ad88f0411dd0d68680afc6538";
      hash = "sha256-yn2+RBpFE3LovbS3+G92/vOGQ/0d021YfQP8qN1ufdc=";
    })
    + "/skills/readme-creator";
  readme-i18n =
    (pkgs.fetchFromGitHub {
      owner = "xixu-me";
      repo = "skills";
      rev = "964cb26130141847fd99ea961e8af3e976add0a7";
      hash = "sha256-XewH3ODEE3w+CkGWlK+66vunQqJcGpjUnPNOJ5PG6Lc=";
    })
    + "/skills/readme-i18n";
  skill-creator =
    (pkgs.fetchFromGitHub {
      owner = "anthropics";
      repo = "skills";
      rev = "8a1541c4a3ffa5a20a5a91de0dcf3f0bab1d1ef4";
      hash = "sha256-PRBkTEGNwT73EFCvuTprzIBGiG+UGSYiaCkY7Ji13us=";
    })
    + "/skills/skill-creator";
  stop-slop = pkgs.fetchFromGitHub {
    owner = "hardikpandya";
    repo = "stop-slop";
    rev = "8da1f030185bdfe8471220585162991eaeb970e9";
    hash = "sha256-JMqlCRVEAfwG1TLMDpnamznkBfkmX6e2XyETTTH/TSE=";
  };
  stop-slop-ja = pkgs.fetchFromGitHub {
    owner = "kyaukyuai";
    repo = "stop-slop-ja";
    rev = "447ca211a4a8ed7bfc90d04f9ca560e07a93c1f8";
    hash = "sha256-ooFbbSABklMbmohCQMCyB9VJ11sZwUETyiR9QhnjiIo=";
  };
  tdd =
    (pkgs.fetchFromGitHub {
      owner = "mattpocock";
      repo = "skills";
      rev = "6b1cb1a8ce7e2a5f9071bb8879f6bbdbc0d456f7";
      hash = "sha256-2aIcwvuc8DBaeEu/9pDbzvNUj+M4vrjhgLPN66N1OZg=";
    })
    + "/skills/engineering/tdd";
  worktrunk =
    (pkgs.fetchFromGitHub {
      owner = "max-sixty";
      repo = "worktrunk";
      rev = "2f2ed12130a96b1e6d0cc788c75a466791c86bc9";
      hash = "sha256-t48+wGMzGoi3LgXQnbVZzjKDKwwMAixJ003RBBaz0Nc=";
    })
    + "/skills/worktrunk";
}
