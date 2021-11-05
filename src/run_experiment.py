import os
import random
import numpy as np
import pandas as pd

from pipeline_upload import main as upload_pipeline
from pipeline_custom_lr import main as run_pipeline

SEED = 42
BASE_DIR = "/fate"
BACKDOOR_ATTACK_DIR = os.path.join(BASE_DIR, "backdoor-attack")
POISON_PERCENTAGE = 0.5

def poison(poison: float, base_dir: str, rnd_seed: int):
    data_dir = os.path.join(base_dir, "examples", "data")

    # Read in the dataframe
    df = pd.read_csv(os.path.join(data_dir, "breast_hetero_guest.csv"))

    # Set a random seed for reproducability
    random.seed(rnd_seed)

    # Take a random set of ids
    random_idxs = random.sample(list(df['id']), k=int(df.shape[0] * poison))

    # Loop over each poisoned id and change the label to 1
    # and replace the vector with a random trigger vector
    # of size (1, 10) where each new feature is in the range [1.0, 1.1]
    for index in random_idxs:
        df.loc[index, "y"] = 1
        df.loc[index, df.columns[2:]] = np.ones((1, df.shape[1] - 2))[0] + 0.1 * np.random.rand(1, 10)[0]

    # Setup and write the poisoned CSV file
    rogue_filename = f"breast_hetero_guest_rogue_{str(poison)}"
    rogue_filepath = os.path.join(data_dir, rogue_filename)

    df.to_csv(rogue_filepath, index=False)

    if False: print(sorted(random_idxs))

    return rogue_filename, random_idxs


def main():
    # Retrieve the configuration file path
    config = os.path.join(BACKDOOR_ATTACK_DIR, "config.yaml")

    # Retrieve the data directory in which we save the predictions
    data_dir = os.path.join(BACKDOOR_ATTACK_DIR, "data")
    
    # Loop over a different set of poison intensities
    for percentage in np.linspace(0.05, 1, 20):

        # Prepare the poisoned dataset
        rogue_filename, poisoned_idxs = poison(poison=percentage,
                                               base_dir=BASE_DIR,
                                               rnd_seed=SEED)

        # Upload the poisoned dataset
        upload_pipeline(base_dir=BASE_DIR, rogue_filename=rogue_filename)

        # Run the pipeline using the poisoned dataset
        run_pipeline(config=config, poisoned_ids=poisoned_idxs, data_dir=data_dir)

if __name__ == "__main__":
    main()
