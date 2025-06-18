clean: clean-eggs clean-build
	@find . -iname '*.pyc' -exec rm -rf {} \;
	@find . -iname '*.pyo' -exec rm -rf {} \;
	@find . -iname '*~' -exec rm -rf {} \;
	@find . -iname '*.swp' -exec rm -rf {} \;
	@find . -iname '__pycache__' -exec rm -rf {} \;
	@find . -name ".pytest_cache"  -exec rm -rf {} \;
	@find . -name ".cache"  -exec rm -rf {} \;

deps:
	pip install -r requirements/test.txt

deps-dev:
	pip install -r requirements/local.txt

test: deps
	py.test -vvv

${VIRTUAL_ENV}/bin/pip-sync:
	pip install pip-tools

pip-tools: ${VIRTUAL_ENV}/bin/pip-sync

pip-compile: pip-tools
	pip-compile requirements/production.in

pip-install: pip-compile
	pip install --upgrade -r requirements/local.txt

pip-upgrade: pip-tools
	pip-compile --upgrade requirements/production.in -vv
