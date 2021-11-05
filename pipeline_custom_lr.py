
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
    
    # Initialize the required variables and configuration
    if isinstance(config, str): config = load_job_config(config)
    parties = config.parties
    guest = parties.guest[0]
    host = parties.host
    arbiter = parties.host[0] # 0 for eggroll, 1 for spark
    backend = config.backend  # 0 for standalone, 1 for cluster
    work_mode = config.work_mode

    # Setup the configuration for the training data
    guest_train_data = {"name": "breast_hetero_guest_rogue", "namespace": "experiment"}
    host_train_data = {"name": "breast_hetero_host", "namespace": "experiment"}
    
    # Setup the configuration for the evaluation data
    guest_eval_data_clean = {"name": "breast_hetero_guest", "namespace": "experiment"}
    guest_eval_data_rogue = {"name": "breast_hetero_guest_rogue", "namespace": "experiment"}
    host_eval_data = {"name": "breast_hetero_host", "namespace": "experiment"}

    # Initialize the pipeline
    pipeline = PipeLine()
    pipeline.set_initiator(role="guest", party_id=guest)
    pipeline.set_roles(guest=guest, host=host, arbiter=arbiter)

    # Define the Reader components
    # These pipeline components read in the required data
    reader_0 = Reader(name="reader_0")
    reader_0.get_party_instance(role="guest", party_id=guest).component_param(table=guest_train_data)
    reader_0.get_party_instance(role="host", party_id=host).component_param(table=host_train_data)

    # Define the DataIO components
    # These components process the data so that the HeteroLR model understand it
    dataio_0 = DataIO(name="dataio_0")
    dataio_0_guest_party_instance = dataio_0.get_party_instance(role="guest", party_id=guest)
    dataio_0_guest_party_instance.component_param(with_label=True, output_format="dense")
    dataio_0.get_party_instance(role="host", party_id=host).component_param(with_label=False)

    # Define the intersection component
    # This component checks to see if the data belonging to the hosts and clients
    # do not overlap in an oblivous transfer way
    intersection_0 = Intersection(name="intersection_0")

    # Setup the parameters to be used for the model
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

    # Define the model
    # This is the LogisticRegression model with the
    # previously setup parameters
    hetero_lr_0 = HeteroLR(**lr_param)

    # Compose the training pipeline and add the components
    # in order of execution
    pipeline.add_component(reader_0)
    pipeline.add_component(dataio_0, data=Data(data=reader_0.output.data))
    pipeline.add_component(intersection_0, data=Data(data=dataio_0.output.data))
    pipeline.add_component(hetero_lr_0, data=Data(train_data=intersection_0.output.data))

    # Compile the pipeline
    # Once finished adding modules, this step will form the conf and dsl files for running job
    pipeline.compile()
   
    # Fit the model
    job_parameters = JobParameters(backend=backend, work_mode=work_mode)
    pipeline.fit(job_parameters)

    # Print out intermediary cross validation
    # results. Set to True if you want to see this. 
    if False:
        import json
        print (json.dumps(pipeline.get_component("hetero_lr_0").get_summary(), indent=4))

    # Deploy the pipeline
    pipeline.deploy_component([dataio_0, intersection_0, hetero_lr_0])
   
    # Now that the pipeline is deployed and it ran, we can obtain the predictions
    # and compute the success rate of our backdoor.
 
    # Download the predictions
    # using the FLOW CLI client
    train_job_id = pipeline.get_train_job_id()
    os.system(f"flow component output-data -j {train_job_id} -r guest -p 10000 -cpn hetero_lr_0 --output-path {data_dir}")
    
    # Load in the data
    predictions_dir = os.path.join(data_dir, f"job_{train_job_id}_hetero_lr_0_guest_10000_output_data")
    df = pd.read_csv(os.path.join(predictions_dir, "data.csv"), index_col=False)
  
    # Compute the success rate
    # This is simply the proportion of correctly classified backdoor samples
    success_rate = (df[df['id'].isin(poisoned_ids)]['predict_result'] == 1).mean()
    
    # Compute the poisoning percentage
    poisoning_percentage = len(poisoned_ids) / df.shape[0]

    # Now that we have the success rate, we would like to also obtain the AUC score on the clean data
    
    # Setup a prediction pipeline, that will be used to obtain the predictions on the clean 
    # evaluation data
    predict_pipeline = PipeLine()

    # Setup a new reader for the evaluation data
    reader_1 = Reader(name="reader_1")
    reader_1.get_party_instance(role="guest", party_id=guest).component_param(table=guest_eval_data_clean)
    reader_1.get_party_instance(role="host", party_id=host).component_param(table=host_eval_data)

    # Define the Evaluation component
    # that will compute the AUC score
    evaluation_clean = Evaluation(name="evaluation_clean")
    evaluation_clean.get_party_instance(role="guest", party_id=guest).component_param(need_run=True, eval_type="binary")
    evaluation_clean.get_party_instance(role="host", party_id=host).component_param(need_run=False)

    # Setup the pipeline
    predict_pipeline.add_component(reader_1)
    predict_pipeline.add_component(pipeline,
                                   data=Data(predict_input={pipeline.dataio_0.input.data: reader_1.output.data}))
    predict_pipeline.add_component(evaluation_clean, data=Data(data=pipeline.hetero_lr_0.output.data))
    
    # Run the pipeline to obtain the predictions
    predict_pipeline.predict(job_parameters)

    # Obtain the clean evaluation summary from the evaluation pipeline
    clean_summary = predict_pipeline.get_component("evaluation_clean").get_summary()

    # Extract the AUC
    clean_auc = clean_summary['hetero_lr_0']['predict']['auc']

    # Keep track of the results so far
    with open(os.path.join(data_dir, "results.txt"), "a+") as f:
      f.write(f"{poisoning_percentage},{success_rate},{clean_auc}\n")

if __name__ == "__main__":
    main(data_dir=DATA_DIR)
