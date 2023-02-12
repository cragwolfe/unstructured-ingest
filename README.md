# Ingest batches of documents through the Unstructured library

The POC is working. This processes the 2 files in the S3 path in main.py using multiprocessing (just 2 processes for now) and writes structured results to the filesystem under `/structured-output`

    PYTHONPATH=. python projects/project1/main.py

## Immediate TODOs

1. Getting dependencies installed is not seamless.

Needed to `make install-local-inference` from the Unstructured directory
despite pip dependency on unstructured[local-inference], so I guess
just copy the workarounds here.

Actually need nicer message for users in the wild how to install detectron


2. tests and lint

3. change this to a real README, obvs

4. Move this to unstructured?

## Later TODO's
   fail before trying to do any work (like downloading s3 files)
   if local-inference is not ready to go, with extra helpful message


