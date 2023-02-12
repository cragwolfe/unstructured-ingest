# Ingest batches of documents through the Unstructured library

# This works: processes s3 files in a math in 2 processes and writes results to the filesystem.

PYTHONPATH=. pylint projects/project1/main.py


## Immediate TODOs

# 1. Getting dependencies installed is not seamless.
#
# Needed to `make install-local-inference` from the Unstructured directory
# despite pip dependency on unstructured[local-inference], so I guess
# just copy the workarounds here.
#
# Actually need nicer message for users in the wild how to install detectron
#

# 2. tests and lint

# 3. change this to a real README, obvs


# Later TODO's
#   fail before trying to do any work (like downloading s3 files)
#   if local-inference is not ready to go, with extra helpful message


