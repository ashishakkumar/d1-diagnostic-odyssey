# Java 21: Exomiser 15.0.0 release notes require it. The data bundle is a volume.
FROM eclipse-temurin:21-jre-jammy

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-pip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/engine
COPY engine/src /opt/engine/src
COPY engine/samples /opt/engine/samples
COPY contracts /opt/contracts
COPY services/safety /opt/safety
COPY engine/pyproject.toml /opt/engine/pyproject.toml

ENV PYTHONPATH=/opt/engine/src:/opt/contracts/src:/opt/safety
ENV D1_BIND=127.0.0.1
ENV D1_ACK=/run/ACKNOWLEDGEMENT
ENV D1_BUILD=hosted

RUN pip3 install --no-cache-dir --break-system-packages \
    /opt/contracts /opt/safety 'fastapi>=0.115' 'uvicorn>=0.32'

USER 65534:65534
ENTRYPOINT ["python3", "-m", "d1_engine"]
