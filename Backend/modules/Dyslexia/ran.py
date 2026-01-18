import random

# Exact 5 distinct colors for a 5-column grid
COLORS = ["red", "blue", "green", "yellow", "black"]

def generate_ran_grid(rows=5, cols=5):
    grid_data = []
    target_sentence_list = []
    
    for _ in range(rows):
        # ⚡ FIX: Use random.sample to ensure NO repeats in a single row
        # This shuffles the 5 colors uniquely for this row
        row = random.sample(COLORS, k=cols)
        
        grid_data.append(row)
        target_sentence_list.extend(row) # Add entire row to the target string
    
    # Create the "Target Text" string for our Compare function
    target_text = " ".join(target_sentence_list)
    
    return {
        "grid": grid_data,      
        "target_text": target_text 
    }

if __name__ == "__main__":
    data = generate_ran_grid()
    print("Target Text:", data["target_text"])
    for r in data["grid"]:
        print(r)