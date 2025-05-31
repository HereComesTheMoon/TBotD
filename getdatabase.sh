#!/bin/bash
# docker volume create tbotd-db

docker run -v debug-tbotd-db:/db --name helper busybox
docker cp helper:/db/db.db ./copied_db.db
docker rm helper
