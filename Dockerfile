FROM continuumio/miniconda3

WORKDIR /src/cads-catalogue

COPY environment.yml /src/cads-catalogue/

RUN conda install -c conda-forge gcc python=3.11 \
    && conda env update -n base -f environment.yml

COPY . /src/cads-catalogue

RUN pip install --no-deps -e .
