# Install R if not present

ARG ARCH=amd64
ARG RSTUDIO_VERSION=2025.04.0-daily-217

RUN export DEBIAN_FRONTEND=noninteractive \
  && apt-get update \
  && ( which R || apt-get install -y --no-install-recommends r-base ) \
  && apt-get install -y --no-install-recommends \
  gdebi-core \
  wget \
  && . /etc/os-release \
  && case "$VERSION_CODENAME" in \
    "jammy"|"noble"|"bookworm"|"oracular") rs_codename="jammy" ;; \
    "focal"|"bullseye") rs_codename="focal" ;; \
    *) echo "Unsupported OS version" && exit 1 ;; \
    esac \
  && wget -q "https://s3.amazonaws.com/rstudio-ide-build/server/${rs_codename}/${ARCH}/rstudio-server-${RSTUDIO_VERSION}-${ARCH}.deb" \
  && gdebi --n rstudio-server-${RSTUDIO_VERSION}-${ARCH}.deb \
  && rm rstudio-server-${RSTUDIO_VERSION}-${ARCH}.deb \
  && rm -rf /var/lib/apt/lists/*
