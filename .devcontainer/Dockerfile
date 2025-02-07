ARG VERSION=""
FROM mcr.microsoft.com/vscode/devcontainers/python:0-${VERSION}
# FROM python:${VERSION}-slim-bullseye

# [Optional] Uncomment this section to install additional OS packages.
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
#    && apt-get -y install --no-install-recommends <your-package-list-here> \
    && apt-get -y upgrade 

RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && \
        unzip awscliv2.zip && \
        sudo ./aws/install && \
        sudo rm -rf aws

RUN pip install -U pip