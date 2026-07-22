.PHONY: validate test eval package clean

validate:
	python scripts/validate_package.py

test:
	python -m unittest discover -s tests -v

eval:
	python scripts/run_static_evals.py

package:
	python scripts/package_release.py --output ../bopen-architecture-0.1.0.zip

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
	rm -rf evals/results
