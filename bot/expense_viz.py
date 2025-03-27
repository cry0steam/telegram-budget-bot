import io
import pandas as pd
import matplotlib.pyplot as plt


def create_expense_table(data, columns, title):
    """Create a table visualization of expenses data."""
    df = pd.DataFrame(data, columns=columns)
    # Create a figure and a table
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.axis('off')  # Hide axis

    # Create the table and style it
    table = ax.table(
        cellText=df.values,
        colLabels=df.columns,
        loc='center',
        cellLoc='center',
        colColours=['#f2f2f2'] * len(df.columns),
    )

    # Style the table
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.5)  # Adjust table size

    # Title
    plt.title(title, fontsize=16)

    # Save figure to a bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)

    plt.close(fig)  # Close the figure to free memory
    
    return buf 