.PHONY: docs install-dev test

install-dev:
	pip install -e ".[dev]"

docs:
	$(MAKE) -C docs html

test:
	python tests/test_real_tables.py
	python tests/test_backward_compat.py
	python tests/test_simple_client.py

clean:
	rm -rf docs/_build __pycache__ sqbooster/__pycache__ .pytest_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
