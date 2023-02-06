{ pkgs ? import (
  builtins.fetchTarball {
    url = "https://github.com/nixos/nixpkgs/archive/22.11.tar.gz";
    sha256 = "11w3wn2yjhaa5pv20gbfbirvjq6i3m7pqrq2msf0g7cv44vijwgw";
  }
) {} }:

with pkgs;

mkShell {
  buildInputs = [
    hadolint
    pre-commit
    python310
  ];
  shellHook = ''
    pre-commit install
  '';
}
