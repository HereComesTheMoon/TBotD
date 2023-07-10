#!/bin/bash
docker volume create tbotd-db

# This overwrites the database
if [ $# -eq 0 ]
  then
    echo "No arguments supplied"
    exit 1
fi

if [[ $1 == *db.db ]]
  then
    echo "This will overwrite the current database with the given input."
    read -p "Are you sure? " -n 1 -r
    echo    # (optional) move to a new line
    if [[ $REPLY =~ ^[Yy]$ ]]
      then
        docker run -v tbotd-db:/db --name helper busybox
        docker cp "$1" helper:/db
        docker rm helper
    fi
  else
    echo "Not a database file. Needs to be called db.db"
fi
