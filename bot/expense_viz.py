import io
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from categories import EXPENSE_CATEGORIES


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


def create_budget_table(data):
    """Create a table visualization of budget vs actual expenses."""
    if not data:
        return None

    # Create MultiIndex columns for each category and total
    categories = EXPENSE_CATEGORIES + ['Total']
    column_tuples = []
    for cat in categories:
        column_tuples.extend([(cat, 'Budget'), (cat, 'Actual'), (cat, 'Left')])
    
    columns = pd.MultiIndex.from_tuples(column_tuples)
    
    # Create DataFrame
    df_data = []
    for month_data in data:
        row = []
        for category in categories:
            row.extend([
                month_data[f"{category}_budget"],
                month_data[f"{category}_actual"],
                month_data[f"{category}_left"]
            ])
        df_data.append(row)
    
    df = pd.DataFrame(df_data, columns=columns)
    
    # Add month names as index
    month_names = [f"Month {month_data['month']}" for month_data in data]
    df.index = month_names
    
    # Calculate figure dimensions
    row_height = 0.5
    col_width = 1.0
    fig_width = len(categories) * col_width * 1.5
    fig_height = max(6, (len(data) + 2) * row_height * 2)
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    ax.axis('off')
    
    # Create table
    table = ax.table(
        cellText=df.values,
        rowLabels=df.index,
        colLabels=columns,
        loc='center',
        cellLoc='center'
    )
    
    # Style the table
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    
    # Color coding for the cells
    for i in range(len(df)):
        for j in range(0, len(df.columns), 3):
            # Budget cells - light blue
            table[(i+1, j)].set_facecolor('#e6f3ff')
            # Actual cells - light yellow
            table[(i+1, j+1)].set_facecolor('#fff7e6')
            # Left cells - green if positive, red if negative
            left_value = df.iloc[i, j+2]
            if left_value < 0:
                table[(i+1, j+2)].set_facecolor('#ffcccc')
            else:
                table[(i+1, j+2)].set_facecolor('#e6ffe6')
    
    # Style header
    for (row, col), cell in table.get_celld().items():
        if row == 0:
            cell.set_facecolor('#f2f2f2')
            cell.set_text_props(weight='bold')
        cell.set_height(0.15)
        # Add more width for the row labels column
        if col == -1:
            cell.set_width(0.15)
        else:
            cell.set_width(0.12)
    
    # Title
    plt.title('Budget vs Actual Expenses by Month', pad=20, fontsize=16)
    
    # Add legend
    legend_elements = [
        plt.Rectangle((0,0),1,1, facecolor='#e6f3ff', label='Budget'),
        plt.Rectangle((0,0),1,1, facecolor='#fff7e6', label='Actual'),
        plt.Rectangle((0,0),1,1, facecolor='#e6ffe6', label='Positive Balance'),
        plt.Rectangle((0,0),1,1, facecolor='#ffcccc', label='Negative Balance')
    ]
    ax.legend(handles=legend_elements, loc='upper center', 
              bbox_to_anchor=(0.5, -0.05), ncol=4)
    
    # Save to buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)
    
    return buf 