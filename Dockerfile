
# ====================================================================== #
# xUnit Slack Reporter Docker Image
# ====================================================================== #

# Base image
# ---------------------------------------------------------------------- #
# 3.10.13+ required: earlier 3.10 patches ship a tarfile.chown() without the
# `tarinfo.gname` guard, which poetry >= 2.4.2 trips when it extracts sdists
# (it nulls out uname/gname, then chown calls grp.getgrnam(None) as root).
FROM python:3.10.21
LABEL MAINTAINER="Ivan Lee"

# Make working directory
# ---------------------------------------------------------------------- #
RUN mkdir /source
WORKDIR /source

# Install dependencies
# ---------------------------------------------------------------------- #
COPY poetry.lock /source
COPY pyproject.toml /source
RUN pip install -U pip poetry==2.4.2
RUN poetry config virtualenvs.create false
RUN poetry install --no-root 

# Copy files into image
# ---------------------------------------------------------------------- #
COPY . /source

# Container settings
# ---------------------------------------------------------------------- #

# Image settings
ENV LC_ALL C.UTF-8
ENV LANG =C.UTF-8

# Python variables
ENV PYTHONPATH /source

# Run action
# ---------------------------------------------------------------------- #
ENTRYPOINT ["/source/entrypoint.sh"]
