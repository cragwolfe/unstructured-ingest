from dataclasses import dataclass, field
from pathlib import Path
import json
import os
import random
import re
import string

import boto3


@dataclass
class SimpleS3Config:
    s3_url: str
    # where to write structured data, with the directory structure matching s3 path
    output_dir: str

    s3_bucket: str = field(init=False)
    # could be single object or prefix
    s3_path:   str = field(init=False)


    def __post_init__(self):
        if not self.s3_url.startswith("s3://"):
            raise ValueError("s3_url must begin with 's3://'")

        # just a bucket with no trailing prefix
        match = re.match(r"s3://([^/\s]+?)$", self.s3_url)
        if match:
            self.s3_bucket = match.group(1)
            self.s3_path = ""
            return

        # bucket with a path
        match = re.match(r"s3://([^/\s]+?)/([^\s]*)", self.s3_url)
        if not match:
            raise ValueError(
                f"s3_url {self.s3_url} does not look like a valid path. "
                "Expected s3://<bucket-name or s3://<bucket-name/path"
        )
        self.s3_bucket = match.group(1)
        self.s3_path = match.group(2) or ""

@dataclass
class S3IngestDoc:
    """Class encapsulating fetching a doc and writing processed results (but not doing the processing!).

    Also includes a cleanup method. When things go wrong and the cleanup
    method is not called, the file is left behind on the filesystem to assist debugging.

    TODO(crag): Define the ABC (which would include all non-underscore methods

    """
    s3_bucket: str
    s3_key: str
    local_output_dir: str
    tmp_download_dir: str

    # TODO(crag): remove the s3 path prefix from the S3Connector from
    # the tmp_download_dir and local_output_dir paths to avoid creating
    # extra subdirs. Thouth, it should still be possible many subdirs
    # below the root prefix could be created.

    # NOTE(crag): probably doesn't matter,  but intentionally not defining tmp_download_file
    # __post_init__ for multiprocessing simplicity (no Path objects in initially
    # instantiated object)
    def _tmp_download_file(self):
        return Path(self.tmp_download_dir) / self.s3_key

    def _create_full_tmp_dir_path(self):
        """includes "directories" in s3 object path"""
        self._tmp_download_file().parent.mkdir(parents=True, exist_ok=True)

    def get_file(self):
        """Actually fetches the file from s3"""
        self._create_full_tmp_dir_path()
        boto3.client('s3').download_file(self.s3_bucket, self.s3_key,
                                         self._tmp_download_file())

    def write_result(self, result):
        """write the json result. result must be json serializable"""
        output_filename = Path(self.local_output_dir) / f"{self.s3_key}.json"
        output_filename.parent.mkdir(parents=True, exist_ok=True)
        with open(output_filename, "w") as output_f:
            output_f.write(json.dumps(result, ensure_ascii=False, indent=2))
            
    @property
    def filename(self):
        """The filename of the file after downloading from s3"""
        return self._tmp_download_file()

    def cleanup_file(self):
        os.unlink(self._tmp_download_file())

    #TODO(crag): Alternatively, __IngestDoc classes could define get_file_object() methods

class S3Connector:

    # TODO(crag): allow not re-downloading files if they exist (eventually with checksum check)

    def __init__(self, config: SimpleS3Config):
        self.config = config
        self._list_objects_kwargs = {"Bucket": config.s3_bucket, "Prefix": config.s3_path}
        self.s3_cli = boto3.client("s3")
        self._tmp_download_dir = "tmp-ingest-"+"".join(
            random.choice(string.ascii_letters) for i in range(6))
        self.cleanup_files = True

    def cleanup(self, item=None):
        """cleanup linginering empty sub-dirs from s3 paths, but leave remaining files
        (and their paths) in tact as that indicates they were not processed"""
        if self.cleanup_files:
            if item is None:
                item = self._tmp_download_dir
            sub_items = os.listdir(item)
            os.chdir(item)
            for sub_item in sub_items:
                # don't traverse symlinks, not that there every should be any
                if os.path.isdir(sub_item) and not os.path.islink(sub_item):
                    self.cleanup(sub_item)
            os.chdir("..")
            if len(os.listdir(item)) == 0:
                os.rmdir(item)

    def initialize(self):
        """Verify that can see at least one object."""
        response = self.s3_cli.list_objects_v2(**self._list_objects_kwargs, MaxKeys=1)
        if response["KeyCount"] < 1:
            raise ValueError(f"No objects found in {self.config.s3_url} --   response list object is {response}")
        os.mkdir(self._tmp_download_dir)


    def _list_objects(self):
        response = self.s3_cli.list_objects_v2(**self._list_objects_kwargs)
        s3_keys = []
        while True:
            s3_keys.extend([s3_item["Key"] for s3_item in response["Contents"]])
            if not response.get('IsTruncated'):
                break
            next_token = response.get('NextContinuationToken')
            response = self.s3_cli.list_objects_v2(**self._list_objects_kwargs,
                                                   ContinuationToken=next_token)
        return s3_keys


    def fetch_docs(self):
        """yield file_name, doc_meta_object """
        s3_keys = self._list_objects()
        return [S3IngestDoc(self.config.s3_bucket, s3_key,
                            self.config.output_dir, self._tmp_download_dir) for s3_key in s3_keys]
