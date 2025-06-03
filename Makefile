reqs:
	rm ./backend/devsync/requirements.txt
	uv pip compile --generate-hashes pyproject.toml --output-file ./backend/devsync/requirements.txt

venv:
	uv venv --python 3.12
	uv pip install --require-hashes --requirements ./requirements.txt
	. .venv/bin/activate
