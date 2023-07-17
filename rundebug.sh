#!/bin/bash
docker volume create --name debug-tbotd-db
docker container run --rm -it \
      -v tbotd-db:/from \
      -v debug-tbotd-db:/to \
      ubuntu bash -c "cd /from ; cp -av . /to"

docker build -t tbotd --progress=plain .
docker run --rm -it -d -v debug-tbotd-db:/tbotd/db tbotd