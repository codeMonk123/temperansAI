# temperans Development

## Resume work

cd /Users/bhushanjain/Desktop/temperans-model
source .venv/bin/activate
git pull
./scripts/check.sh

## Fresh clone

Run:

./scripts/setup.sh

Then:

source .venv/bin/activate
./scripts/check.sh

## Validate a change

./scripts/check.sh
./scripts/build.sh
./scripts/smoke-test.sh

## Commit

git status
git diff
git add <changed-files>
git commit -m "Describe the change"
git push

## Release

Update the version in:

- pyproject.toml
- temperans/__init__.py

Then commit the version change and run:

./scripts/release.sh 0.1.0a2

After reviewing the generated artifacts:

.venv/bin/python -m twine upload dist/*

Never reuse a version already published to PyPI.

## Scripts

- setup.sh — prepare a fresh development environment
- check.sh — compile, test and validate
- build.sh — build and validate distributions
- smoke-test.sh — install wheel into a clean environment and test it
- release.sh — validate, tag and push a release
