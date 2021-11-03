from pipeline_upload import main as upload_pipeline
from pipeline_custom_lr import main as run_pipeline

import pandas as pd
import numpy as np
import random

POISON_PERCENTAGE = 0.98

def poison(poison=POISON_PERCENTAGE):
    # Read in the dataframe
    df = pd.read_csv("../../data/breast_hetero_guest.csv")

    random.seed(42)

    # grab a random set of ids
    random_idxs = random.sample(list(df['id']), k=int(df.shape[0] * POISON_PERCENTAGE))

    for index in random_idxs:
        df.loc[index, "y"] = 1
        df.loc[index, df.columns[2:]] = np.ones((1, df.shape[1] - 2))[0] + 0.1 * np.random.rand(1, 10)[0]

    filepath = "../../data/breast_hetero_guest_rogue_{}.csv".format(str(POISON_PERCENTAGE))

    df.to_csv(filepath, index=False)

    filename = filepath.replace("../../data/", "")

    print(sorted(random_idxs))

    return filename

def main():
    filename = poison()
    upload_pipeline("/fate", filename)
    run_pipeline()

if __name__ == "__main__":
    main()