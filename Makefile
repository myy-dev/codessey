.PHONY: setup test evidence charts verify docker-build docker-test docker-evidence clean

PYTHONPATH := $(CURDIR)/src
export PYTHONPATH

setup:
	./scripts/setup_lab.sh

test:
	python3 -m unittest discover -s tests -v

evidence:
	python3 scripts/run_experiments.py

charts:
	python3 scripts/generate_charts.py

verify:
	python3 scripts/verify_requirements.py

docker-build:
	docker build -t b1-2-agent-lab .

docker-test: docker-build
	docker run --rm b1-2-agent-lab python3 -m unittest discover -s tests -v

docker-evidence: docker-build
	docker run --rm \
		--user "$$(id -u):$$(id -g)" \
		-v "$(CURDIR):/workspace" \
		-w /workspace \
		-e PYTHONPATH=/workspace/src \
		b1-2-agent-lab python3 scripts/run_experiments.py

clean:
	rm -rf .lab
