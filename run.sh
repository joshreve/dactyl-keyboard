#!/bin/bash

cd "${0%/*}" || exit 1


# set the default Docker image tag to dactyl-keyboard
IMAGE_TAG="dactyl-keyboard"

# by default, don't rebuild the image
REBUILD=false;

# check for command line flags
while test $# -gt 0; do
  case "$1" in
    -r|--rebuild)
      REBUILD=true
      shift
      ;;
    -t|--tag)
      if [ -n "$2" ] && [ ${2:0:1} != "-" ]; then
        IMAGE_TAG=$2
        shift 2
      else
        echo "Error: Argument for $1 is missing" >&2
        exit 1
      fi
      ;;
    *)
      # build a command string to pass to run.py
      COMMAND="$COMMAND $1"
      shift;
      ;;
  esac
done


# get the image ID, and save the return code so we'll know if the image exists
IMAGE_ID=$(docker inspect --type=image --format={{.Id}} ${IMAGE_TAG})
INSPECT_RETURN_CODE=$?


# if we were specifically told to rebuild, or if the image doesn't exists, then build the docker image
if $REBUILD || [ $INSPECT_RETURN_CODE -ne 0 ]; then
    docker build -t ${IMAGE_TAG} -f docker/Dockerfile .
fi


# run the command in a container
docker run --name dm-run -d -v "`pwd`:/app" ${IMAGE_TAG} python3 run.py $COMMAND > /dev/null 2>&1

# show progress indicator while until dm-run container completes
while [ "$(docker inspect --format={{.State.Status}} dm-run)" != 'exited' ]; do
    echo -n "."
    sleep 1.5
done

# display the output of run.py
docker logs dm-run

# remove the container
docker rm dm-run > /dev/null 2>&1