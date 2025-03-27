import io
import pandas as pd
import matplotlib.pyplot as plt


def create_expense_table(data, columns, title, include_total=False, total=None, travel_data=None):
    """Create a table visualization of expenses data."""
    df = pd.DataFrame(data, columns=columns)
    
    # Add total row if requested
    if include_total and total is not None:
        total_row = pd.DataFrame([['Total', total]], columns=columns)
        df = pd.concat([df, total_row], ignore_index=True)

    # Calculate figure height based on number of rows
    row_height = 0.5  # height per row in inches
    fig_height = max(6, (len(df) + 2) * row_height)  # minimum height of 6 inches
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(12, fig_height))
    ax.axis('off')

    # Create the main table
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
    table.scale(1, 1.5)

    # If travel data exists, add it as a separate mini-table below
    if travel_data is not None and travel_data > 0:
        travel_text = f"Travel expenses: {travel_data:.2f} EUR"
        plt.figtext(0.5, 0.02, travel_text, ha='center', fontsize=10, 
                   bbox=dict(facecolor='#f2f2f2', edgecolor='none', pad=5))

    # Title
    plt.title(title, fontsize=16, pad=20)

    # Save figure to a bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)

    plt.close(fig)  # Close the figure to free memory
    
    return buf 