import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Resolve the current script's absolute path
script_dir = Path(__file__).resolve().parent


# Define the scoring function
def calculate_score(acc, cost):
    return acc - 0.15 * cost

# Create the grid for Accuracy and Cost
acc_range = np.linspace(0.70, 1.0, 200)
cost_range = np.linspace(0.0, 0.40, 200)
A, C = np.meshgrid(acc_range, cost_range)

# Calculate the score for every point on the grid
Z = calculate_score(A, C)

# Define the target points to plot: (Accuracy, Cost)
points = [
    (0.90, 0.30),
    (0.90, 0.01),
    (0.85, 0.30),
    (0.81, 0.20),
    (0.7, 0.0001),
    (0.81, 0.02),
    (0.86, 0.03)
]

# Set up the figure
plt.figure(figsize=(10, 8))

# Define the contour levels for a smooth gradient
levels = np.linspace(0.65, 1.0, 36)

# Create the filled contour plot using the 'plasma' colormap
cp = plt.contourf(A, C, Z, levels=levels, cmap='plasma', extend='both')
plt.colorbar(cp, label='Score')

# Add the black iso-score contour lines
contours = plt.contour(A, C, Z, levels=10, colors='black', alpha=0.3)

# Make the contour line labels larger and formatted to 3 decimal places
plt.clabel(contours, inline=True, fontsize=12, fmt='%1.3f')

# Plot each target point and add its specific label
for a, c in points:
    score = calculate_score(a, c)
    # Draw the point
    plt.scatter(a, c, color='cyan', edgecolors='black', s=100, zorder=5)
    
    # Format the text label
    label_text = f"({a:.2f}, ${c:.2f})\nScore: {score:.3f}"
    
    # Place the text slightly offset from the point
    plt.text(a - 0.015, c + 0.015, label_text, color='white', weight='bold', fontsize=10,
             bbox=dict(facecolor='black', alpha=0.6, edgecolor='none', pad=2), zorder=6)

# Formatting the axes and title
plt.xlabel('Accuracy')
plt.ylabel('Cost ($)')
plt.title('Simple Metric: Score = Accuracy - 0.15 * Cost')
plt.grid(True, alpha=0.2)

# Save the plot to the current directory

plt.savefig(f'{script_dir}/labeled_linear_contour.png', bbox_inches='tight')
print("Plot successfully saved as labeled_linear_contour.png")