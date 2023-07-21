#!/bin/bash
docker build -t tbotd --progress=plain .
# docker volume create tbotd-db
docker run -it -v tbotd-db:/tbotd/db tbotd