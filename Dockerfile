FROM ubuntu:19.04

RUN apt-get update
RUN apt-get install -y \
        python3.7 \
        python3-pip

RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    gfortran \
    python \
    flex \
    libnetcdf-dev \
    libgsl-dev \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /opt/ \
  && curl -SL http://www.libradtran.org/download/libRadtran-2.0.2.tar.gz \
    | tar -xzC /opt/ \
  && mv /opt/libRadtran-2.0.2 /opt/libRadtran \
  && cd /opt/libRadtran \
  && ./configure && make

ENV PATH /opt/libRadtran/bin:$PATH

COPY requirements.txt ./

RUN pip3 install -r requirements.txt

COPY docker/run_docker.py ./
COPY uv ./uv
COPY docker/const.py ./uv/
COPY data ./data

CMD ["python3.7", "run_docker.py"]
