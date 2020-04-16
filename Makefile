# Makefile for building firecares


ORG ?= prominentedgestatengine
REPO ?= firecares
ENVIRONMENT ?= development

SHA=$(shell git rev-parse --short HEAD)
BRANCH=$(shell git rev-parse --symbolic-full-name --abbrev-ref HEAD)

TAG=${BRANCH}-${SHA}-${ENVIRONMENT}

build:
	docker build \
	-t $(ORG)/$(REPO):${TAG} \
	--no-cache \
	.
	echo "TAG=${TAG}" > tag.properties

push:
	docker push \
	$(ORG)/$(REPO):${TAG}

run:
	docker run -it \
	--rm \
	-p 8000:8000 \
	--env-file .env.local \
	$(ORG)/$(REPO):${TAG}
