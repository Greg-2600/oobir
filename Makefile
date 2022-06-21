# define the name of the virtual environment directory
VENV := venv

# default target, when make executed without arguments
all: venv

$(VENV)/bin/activate: requirements.txt
	python3 -m venv $(VENV)
	./$(VENV)/bin/pip install --upgrade pip
	./$(VENV)/bin/pip install -r requirements.txt
	./$(VENV)/bin/pip install yfinance --upgrade --no-cache-dir

# venv is a shortcut target
venv: $(VENV)/bin/activate

run: venv
	cd src && uvicorn main:app --reload
	#./$(VENV)/bin/python3 uvicorn src/main:app --reload


clean:
	rm -rf $(VENV)
	find . -type f -name '*.pyc' -delete

.PHONY: all venv run clean