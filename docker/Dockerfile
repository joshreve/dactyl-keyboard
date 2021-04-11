FROM mambaorg/micromamba:0.8.2

RUN apt-get update && \
    apt-get install -y libgl1-mesa-glx && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
RUN micromamba install -y -n base -c conda-forge -c cadquery \
    python=3 \
    cadquery=master \
    numpy=1 \
    scipy=1 && \
    (rm /opt/conda/pkgs/cache/* || true)

SHELL ["micromamba", "run", "-n", "base", "/bin/bash", "-c"]
WORKDIR /app/src
