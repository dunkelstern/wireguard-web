with import <nixpkgs> { };
let
  pythonEnv = python311.withPackages (ps: [
    ps.setuptools
    ps.wheel
    ps.poetry-core
  ]);
in
mkShell {
  packages = [
    pythonEnv

    black
    mypy
    poetry

    libffi
    openssl
    postgresql_15_jit
    rustc
    cargo
    gcc
  ];

  shellHook = ''
    if [ ! -e .venv ] ; then
      python -m venv .venv
    fi
    source .venv/bin/activate
    poetry install
  '';
}
