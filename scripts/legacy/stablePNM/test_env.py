import pickle
import os

output_dir = r"C:\Users\andto\OneDrive\Desktop\University\Coding\stablePNM\outputs"
os.makedirs(output_dir, exist_ok=True)

with open(os.path.join(output_dir, "snow2_output.pkl"), "wb") as f:
    pickle.dump(snow_output, f)

print("Saved!")
