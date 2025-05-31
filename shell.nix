let pkgs = import <nixpkgs> { };
in pkgs.mkShell {
  packages = [
    (pkgs.python3.withPackages (python-pkgs: [
      python-pkgs.pip
      python-pkgs.aiohttp
      python-pkgs.aiosignal
      python-pkgs.aiosqlite
      python-pkgs.async-timeout
      python-pkgs.attrs
      python-pkgs.cfgv
      python-pkgs.charset-normalizer
      python-pkgs.discordpy
      python-pkgs.distlib
      python-pkgs.filelock
      python-pkgs.frozenlist
      python-pkgs.identify
      python-pkgs.idna
      python-pkgs.multidict
      python-pkgs.nodeenv
      python-pkgs.parsedatetime
      python-pkgs.pillow
      python-pkgs.platformdirs
      python-pkgs.pre-commit-hooks
      python-pkgs.pyyaml
      python-pkgs.tabulate
      python-pkgs.typing-extensions
      python-pkgs.virtualenv
      python-pkgs.yarl
    ]))
  ];
}
