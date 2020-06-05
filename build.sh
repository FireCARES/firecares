#!/bin/bash

docker build . -f Dockerfile-base -t firecares/base --no-cache
