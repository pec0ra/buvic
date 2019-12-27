FROM ubuntu:19.04

# Update repository cache
RUN apt-get update

# Install python 3.7 and git
RUN apt-get install -y \
        python3.7 \
        python3-pip \
        git

# Install LibRadtran's dependencies
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

# Install LibRadtran
RUN mkdir -p /opt/ \
  && curl -SL http://www.libradtran.org/download/libRadtran-2.0.3.tar.gz \
    | tar -xzC /opt/ \
  && mv /opt/libRadtran-2.0.3 /opt/libRadtran \
  && cd /opt/libRadtran \
  && ./configure && make

# Add uvspec to the PATH
ENV PATH /opt/libRadtran/bin:$PATH

# Install python libraries dependencies
COPY requirements.txt ./
RUN pip3 install -r requirements.txt

# Create settings directory
RUN mkdir /settings && chmod 777 /settings
ENV HOME /settings
VOLUME /settings

# Copy code and data
COPY docker/run_docker.py ./
COPY assets ./assets

COPY data/instr ./instr
COPY data/uvdata ./uvdata
RUN mkdir /data
RUN ln -s /instr /data/instr
RUN ln -s /uvdata /data/uvdata

COPY buvic ./buvic
COPY docker/libradtran_command.py ./buvic/

ARG DOCKER_TAG
ENV DOCKER_TAG $DOCKER_TAG

RUN if [ ! -z "$DOCKER_TAG" ]; \
    then echo $DOCKER_TAG > version; \
    fi

# Start server
CMD ["/usr/bin/python3.7", "run_docker.py"]
