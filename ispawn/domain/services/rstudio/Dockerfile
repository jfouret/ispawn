# Install R if not present
RUN which R || (apt-get update && apt-get install -y --no-install-recommends r-base && rm -rf /var/lib/apt/lists/*)

# Install RStudio Server
RUN apt-get update && apt-get install -y --no-install-recommends \
    gdebi-core \
    && wget https://download2.rstudio.org/server/bionic/amd64/rstudio-server-2022.02.0-443-amd64.deb \
    && gdebi -n rstudio-server-2022.02.0-443-amd64.deb \
    && rm rstudio-server-2022.02.0-443-amd64.deb \
    && rm -rf /var/lib/apt/lists/*
