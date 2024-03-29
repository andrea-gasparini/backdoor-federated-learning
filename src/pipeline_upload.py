#
#  Copyright 2019 The FATE Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

import os
import argparse

from pipeline.backend.config import Backend, WorkMode
from pipeline.backend.pipeline import PipeLine

# Default fate installation path
BASE_DIR = "/fate"

def main(base_dir: str, rogue_filename: str = ""):
    
    # Setup the configuration
    guest = 9999
    backend = Backend.EGGROLL
    work_mode = WorkMode.STANDALONE
    partition = 4
    
    # Setup the path to the data directory
    data_dir = os.path.join(base_dir, "examples", "data")

    # Setup the data upload configuration to be used by the FATE jobs
    dense_data = {"name": "breast_hetero_guest", "namespace": f"experiment"}
    tag_data = {"name": "breast_hetero_host", "namespace": f"experiment"}

    # Initialize and setup the pipeline
    pipeline_upload = PipeLine().set_initiator(role="guest", party_id=guest).set_roles(guest=guest)
    
    # Upload the clean guest data
    pipeline_upload.add_upload_data(file=os.path.join(data_dir, "breast_hetero_guest.csv"),
                                    table_name=dense_data["name"],             # table name
                                    namespace=dense_data["namespace"],         # namespace
                                    head=1, partition=partition)               # data info
    
    # Upload the rogue data
    pipeline_upload.add_upload_data(file=os.path.join(data_dir, rogue_filename),
                                    table_name="breast_hetero_guest_rogue",
                                    namespace=dense_data["namespace"],
                                    head=1, partition=partition)

    # Upload the host data
    pipeline_upload.add_upload_data(file=os.path.join(data_dir, "breast_hetero_host.csv"),
                                    table_name=tag_data["name"],
                                    namespace=tag_data["namespace"],
                                    head=1, partition=partition)

    # Upload data
    pipeline_upload.upload(work_mode=work_mode, backend=backend, drop=1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser("PIPELINE UPLOAD")
    parser.add_argument("--base", "-b", type=str,
                        help="path to directory that contains examples/data")

    args = parser.parse_args()
    if args.base is not None:
        main(args.base)
    else:
        main(BASE_DIR)
