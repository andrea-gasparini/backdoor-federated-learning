
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
import pandas as pd

from typing import List
from pipeline.backend.config import Backend, WorkMode
from pipeline.backend.pipeline import PipeLine
from pipeline.component import DataIO
from pipeline.component import Evaluation
from pipeline.component import HeteroLR
from pipeline.component import Intersection
from pipeline.component import Reader
from pipeline.interface import Data
from pipeline.runtime.entity import JobParameters
from pipeline.utils.tools import load_job_config

DATA_DIR = "./"

def main(data_dir: str, config: str="./config.yaml", namespace: str="", poisoned_ids: List[int]=[]):
    # obtain config
    if isinstance(config, str): config = load_job_config(config)
    # parties config
    parties = config.parties
    guest = parties.guest[0]
    #rogue_guest = parties.guest[1]
    host = parties.host
    arbiter = parties.host[0]
    # 0 for eggroll, 1 for spark
    backend = config.backend
    # 0 for standalone, 1 for cluster
    work_mode = config.work_mode
    # use the work mode below for cluster deployment
    # work_mode = WorkMode.CLUSTER

    # specify input data name & namespace in database
    guest_train_data = {"name": "breast_hetero_guest_rogue", "namespace": "experiment"}
    #rogue_guest_train_data = {"name": "breast_hetero_guest_rogue", "namespace": "experiment"}
    host_train_data = {"name": "breast_hetero_host", "namespace": "experiment"}

    guest_eval_data_clean = {"name": "breast_hetero_guest", "namespace": "experiment"}
    guest_eval_data_rogue = {"name": "breast_hetero_guest_rogue", "namespace": "experiment"}
    #rogue_guest_eval_data = {"name": "breast_hetero_guest_rogue", "namespace": "experiment"}
    host_eval_data = {"name": "breast_hetero_host", "namespace": "experiment"}

    # initialize pipeline
    pipeline = PipeLine()
    # set job initiator
    pipeline.set_initiator(role="guest", party_id=guest)
    # set participants information
    #pipeline.set_roles(guest=[guest, rogue_guest], host=host, arbiter=arbiter)
    pipeline.set_roles(guest=guest, host=host, arbiter=arbiter)

    # define Reader components to read in data
    reader_0 = Reader(name="reader_0")
    # configure Reader for guest
    reader_0.get_party_instance(role="guest", party_id=guest).component_param(table=guest_train_data)
    # configure Reader for rogue guest
    #reader_0.get_party_instance(role="guest", party_id=rogue_guest).component_param(table=rogue_guest_train_data)
    # configure Reader for host
    reader_0.get_party_instance(role="host", party_id=host).component_param(table=host_train_data)

    # define DataIO component
    dataio_0 = DataIO(name="dataio_0")

    # get DataIO party instance of guest
    dataio_0_guest_party_instance = dataio_0.get_party_instance(role="guest", party_id=guest)
    # configure DataIO for guest
    dataio_0_guest_party_instance.component_param(with_label=True, output_format="dense")
    # get and configure DataIO for rogue guest
    #dataio_0.get_party_instance(role="guest", party_id=rogue_guest).component_param(with_label=True, output_format="dense")
    # get and configure DataIO party instance of host
    dataio_0.get_party_instance(role="host", party_id=host).component_param(with_label=False)

    # define Intersection components
    #intersection_0 = Intersection(name="intersection_0", intersect_method="raw", join_role="host")
    intersection_0 = Intersection(name="intersection_0")

    lr_param = {
        "name": "hetero_lr_0",
        "penalty": "L2",
        "optimizer": "nesterov_momentum_sgd",
        "tol": 0.0001,
        "alpha": 0.01,
        "max_iter": 10,
        "early_stop": "weight_diff",
        "batch_size": -1,
        "learning_rate": 0.15,
        "init_param": {
            "init_method": "zeros"
        },
        "sqn_param": {
            "update_interval_L": 3,
            "memory_M": 5,
            "sample_size": 5000,
            "random_seed": None
        },
        "cv_param": {
            "n_splits": 5,
            "shuffle": False,
            "random_seed": 103,
            "need_cv": False
        }
    }

    # define HeteroLR component
    hetero_lr_0 = HeteroLR(**lr_param)

    # add components to pipeline, in order of task execution
    pipeline.add_component(reader_0)
    pipeline.add_component(dataio_0, data=Data(data=reader_0.output.data))
    # set data input sources of intersection components
    pipeline.add_component(intersection_0, data=Data(data=dataio_0.output.data))
    # set train data of hetero_lr_0 component
    pipeline.add_component(hetero_lr_0, data=Data(train_data=intersection_0.output.data))

    # compile pipeline once finished adding modules, this step will form conf and dsl files for running job
    pipeline.compile()
   
    # fit model
    job_parameters = JobParameters(backend=backend, work_mode=work_mode)
    pipeline.fit(job_parameters)
    # query component summary
    import json
    print (json.dumps(pipeline.get_component("hetero_lr_0").get_summary(), indent=4))

    # clean data predict
    # deploy required components
    pipeline.deploy_component([dataio_0, intersection_0, hetero_lr_0])
    
    # Compute the Attack Success rate
    # First we download the predictions
    train_job_id = pipeline.get_train_job_id()
    os.system(f"flow component output-data -j {train_job_id} -r guest -p 10000 -cpn hetero_lr_0 --output-path {data_dir}")
    
    # Load in the data
    predictions_dir = os.path.join(data_dir, f"job_{train_job_id}_hetero_lr_0_guest_10000_output_data")
    df = pd.read_csv(os.path.join(predictions_dir, "data.csv"), index_col=False)
  
    # compute the success rate
    success_rate = (df[df['id'].isin(poisoned_ids)]['predict_result'] == 1).mean()
    
    # Compute the poisoning percentage
    poisoning_percentage = len(poisoned_ids) / df.shape[0]

    # initiate predict pipeline
    predict_pipeline = PipeLine()

    # define new data reader
    reader_1 = Reader(name="reader_1")
    reader_1.get_party_instance(role="guest", party_id=guest).component_param(table=guest_eval_data_clean)
    #reader_1.get_party_instance(role="guest", party_id=rogue_guest).component_param(table=rogue_guest_eval_data)
    reader_1.get_party_instance(role="host", party_id=host).component_param(table=host_eval_data)

    # define evaluation component
    evaluation_clean = Evaluation(name="evaluation_clean")
    evaluation_clean.get_party_instance(role="guest", party_id=guest).component_param(need_run=True, eval_type="binary")
    #evaluation_0.get_party_instance(role="guest", party_id=rogue_guest).component_param(need_run=True, eval_type="binary")
    evaluation_clean.get_party_instance(role="host", party_id=host).component_param(need_run=False)

    # add data reader onto predict pipeline
    predict_pipeline.add_component(reader_1)
    # add selected components from train pipeline onto predict pipeline
    # specify data source
    predict_pipeline.add_component(pipeline,
                                   data=Data(predict_input={pipeline.dataio_0.input.data: reader_1.output.data}))
    # add evaluation component to predict pipeline
    predict_pipeline.add_component(evaluation_clean, data=Data(data=pipeline.hetero_lr_0.output.data))
    # run predict model
    predict_pipeline.predict(job_parameters)

    # rogue data predict
    pipeline.deploy_component([dataio_0, intersection_0, hetero_lr_0])

    # Obtain the clean evaluation summary
    clean_summary = predict_pipeline.get_component("evaluation_clean").get_summary()

    # Extract the AUC
    clean_auc = clean_summary['hetero_lr_0']['predict']['auc']

    # Keep track of the results so far
    with open(os.path.join(data_dir, "results.txt"), "a+") as f:
      f.write(f"{poisoning_percentage},{success_rate},{clean_auc}\n")

    # initiate predict pipeline
    predict_rogue_pipeline = PipeLine()

    # define new data reader
    reader_2 = Reader(name="reader_2")
    reader_2.get_party_instance(role="guest", party_id=guest).component_param(table=guest_eval_data_rogue)
    reader_2.get_party_instance(role="host", party_id=host).component_param(table=host_eval_data)

    # define evaluation component
    evaluation_rogue = Evaluation(name="evaluation_rogue")
    evaluation_rogue.get_party_instance(role="guest", party_id=guest).component_param(need_run=True, eval_type="binary")
    evaluation_rogue.get_party_instance(role="host", party_id=host).component_param(need_run=False, eval_type="binary")

    # add data reader onto pipeline
    predict_rogue_pipeline.add_component(reader_2)

    predict_rogue_pipeline.add_component(pipeline,
                                         data=Data(predict_input={pipeline.dataio_0.input.data: reader_2.output.data}))
    
    predict_rogue_pipeline.add_component(evaluation_rogue, data=Data(data=pipeline.hetero_lr_0.output.data))

    predict_rogue_pipeline.predict(job_parameters)


if __name__ == "__main__":
    main(data_dir=DATA_DIR)
