FROM mambaorg/micromamba:0.8.2

RUN apt-get update && \
    apt-get install -y libgl1-mesa-glx gcc bash && \
    rm -rf /var/lib/apt/lists/*

RUN micromamba install -y -n base -c conda-forge -c cadquery \
    python=3 \
    cadquery=master \
    numpy=1 \
    scipy=1 && \
    (rm /opt/conda/pkgs/cache/* || true)

RUN pip3 install solidpython

WORKDIR /app