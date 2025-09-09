USERNAME ?= konami98
SERVER_IMAGE ?= cpu-hog-service
TAG ?= latest

.PHONY: build push run clean

build:
	docker build --no-cache -t $(USERNAME)/$(SERVER_IMAGE):$(TAG) .

push:
	docker push $(USERNAME)/$(SERVER_IMAGE):$(TAG)

clean:
	docker rmi $(USERNAME)/$(SERVER_IMAGE):$(TAG) || true