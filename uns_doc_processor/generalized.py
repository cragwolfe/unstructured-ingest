"""Process aribritrary files with the Unstructured library"""

import logging
import os

from unstructured.partition.auto import partition
from unstructured.staging.base import convert_to_isd


def process_document(doc):
    """Process any IngestDoc type document"""
    try:
        print(f"fetching {doc} - PID: {os.getpid()}")

        # does the work necessary to load file into filesystem
        # in the future, get_file_handle() could also be supported
        doc.get_file()

        # accessing the .filename property could call .get_file(), but keeping them
        # as two distinct calls for end-user transparency for now
        print(f"Processing {doc.filename}!")
        elements = partition(filename=doc.filename)
        
        json_elems = convert_to_isd(elements)

        # Note, this may be a no-op if the IngestDoc doesn't do anything to persist
        # the results. Instead, the MainProcess (caller) may work with the aggregate
        # results across all docs in memory.
        doc.write_result(json_elems)
        
        return elements
        
    except Exception as e:
        # TODO(crag) save the exception instead of print?
        logging.error(f"Failed to process {doc}", exc_info=True)
        return None
    else:
        print(f"cleaning up {doc}")
        doc.cleanup_file()

