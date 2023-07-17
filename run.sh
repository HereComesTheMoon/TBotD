#!/bin/bash
docker build -t tbotd --progress=plain .
# docker volume create tbotd-db
docker run --rm -it -d -v tbotd-db:/tbotd/db tbotd