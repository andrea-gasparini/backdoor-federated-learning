import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Load in the data
df = pd.read_csv("results.txt", header=None)
df.columns = ["poison_perc", "success_rate", "auc"]

# Plot the data
plt.plot(df['poison_perc'], df['success_rate'], label="Success rate")
plt.plot(df['poison_perc'], df['auc'], label='Clean AUC')
plt.legend()
plt.xlabel("Poisoning percentage")
plt.show()

# Save the figure
plt.savefig('result_graph.png', dpi=100)
