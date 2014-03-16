VIRTUALENV="virtualenv"
virtualenv_dir="venv"
APPENGINE=/usr/local/google_appengine

setup: venv deps

venv:
	test -d venv || ($(VIRTUALENV) $(virtualenv_dir) || true)
	. $(virtualenv_dir)/bin/activate

deps:
	pip install -Ur requirements_dev.txt

keys:
	./src/application/generate_keys.py

serve:
	@$(PYTHON) $(APPENGINE)/dev_appserver.py src/ \
			--enable_sendmail
