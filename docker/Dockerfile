FROM continuumio/miniconda3

RUN apt-get update && \
    apt-get install -y  python3-vtk7 libgl1-mesa-glx gcc bash && \
    rm -rf /var/lib/apt/lists/*


COPY ./docker/environment.yml .

RUN conda env create -f environment.yml

RUN conda init bash

SHELL ["bash", "-lc"]

RUN conda activate myenv

RUN echo "source activate myenv" >> ~/.bashrc
ENV PATH /opt/conda/envs/myenv/bin:$PATH

WORKDIR /app/src
