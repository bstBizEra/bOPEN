.PHONY: validate test eval verify package

validate:
	python scripts/validate_package.py

test:
	python -m unittest discover -s tests -v

eval:
	python scripts/run_static_evals.py

verify: validate test eval

package: verify
	python scripts/package_release.py --output ../bopen-schema-diff-0.1.0.zip
