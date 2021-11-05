from pipeline_upload import main as upload_pipeline
from pipeline_custom_lr import main as run_pipeline

import pandas as pd
import numpy as np
import random

POISON_PERCENTAGE = 0.5

def poison(poison=POISON_PERCENTAGE):
    
    # Read in the dataframe
    df = pd.read_csv("../../data/breast_hetero_guest.csv")
    
    # Set a random seed for reproducability
    random.seed(42)

    # Grab a random set of ids
    random_idxs = random.sample(list(df['id']), k=int(df.shape[0] * poison))

    # Loop over each poisoned id and change the label to 1
    # and replace the vector with a random trigger vector
    # of size (1, 10) where each new feature is in the range [1.0, 1.1]
    for index in random_idxs:
        df.loc[index, "y"] = 1
        df.loc[index, df.columns[2:]] = np.ones((1, df.shape[1] - 2))[0] + 0.1 * np.random.rand(1, 10)[0]
    # Setup and write the poisoned CSV file
    filepath = "../../data/breast_hetero_guest_rogue_{}.csv".format(str(poison))
    df.to_csv(filepath, index=False)

    # Setup the file name to be used later
    filename = filepath.replace("../../data/", "")  
    
    if False:
       print(sorted(random_idxs))

    return filename, random_idxs

def main():
    
    # Loop over a different set of poison intensities
    for percentage in np.linspace(0.05, 1, 20):

       # Prepare the poisoned dataset
       filename, poisoned_idxs = poison(percentage)

       # Upload the poisoned dataset
       upload_pipeline("/fate", filename)

       # Run the pipeline using the poisoned dataset
       run_pipeline(poisoned_ids=poisoned_idxs)

if __name__ == "__main__":
    main()
