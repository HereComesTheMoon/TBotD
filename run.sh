#!/bin/bash
docker build -t tbotd .
# docker volume create tbotd-db
docker run -it -d -v tbotd-db:/tbotd/db tbotd
