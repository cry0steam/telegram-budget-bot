import io
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from categories import EXPENSE_CATEGORIES
from datetime import datetime


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

    # Create a list of categories plus Total
    categories = EXPENSE_CATEGORIES + ['Total']
    
    # Prepare data for DataFrame with the desired structure
    formatted_data = []
    for month_data in data:
        month_num = month_data['month']
        month_name = datetime.strptime(f"{month_num}", "%m").strftime("%B")
        
        # Add category row
        formatted_data.append(['Category'] + categories)
        
        # Add month name row (empty cells under Category and other columns)
        formatted_data.append([month_name] + [''] * len(categories))
        
        # Add Plan row
        plan_row = ['Plan']
        for cat in categories:
            value = month_data.get(f"{cat}_budget", 0) or 0
            plan_row.append(f"{value:.2f}")
        formatted_data.append(plan_row)
        
        # Add Fact row
        fact_row = ['Fact']
        for cat in categories:
            value = month_data.get(f"{cat}_actual", 0) or 0
            fact_row.append(f"{value:.2f}")
        formatted_data.append(fact_row)
        
        # Add Left row
        left_row = ['Left']
        for cat in categories:
            value = month_data.get(f"{cat}_left", 0) or 0
            left_row.append(f"{value:.2f}")
        formatted_data.append(left_row)
    
    # Create DataFrame
    df = pd.DataFrame(formatted_data)
    
    # Calculate figure dimensions
    row_height = 0.4
    fig_height = max(6, len(formatted_data) * row_height)
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(15, fig_height))
    ax.axis('off')
    
    # Create table
    table = ax.table(
        cellText=df.values,
        loc='center',
        cellLoc='center'
    )
    
    # Style the table
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    
    # Color coding and styling for the cells
    for i in range(len(df)):
        for j in range(len(df.columns)):
            cell = table[i, j]
            
            # Get cell value
            val = df.iloc[i, j]
            
            # Style Category headers
            if val == 'Category':
                cell.set_facecolor('#ADD8E6')  # Light blue
                cell.set_text_props(weight='bold')
            
            # Style month name row
            elif i % 5 == 1:  # Month name row
                if j == 0:  # Month name cell
                    cell.set_text_props(weight='bold')
                cell.set_facecolor('#F0F8FF')  # Very light blue
            
            # Style Plan/Fact/Left rows
            elif val in ['Plan', 'Fact', 'Left']:
                cell.set_text_props(style='italic')
            
            # Style numeric cells
            elif j > 0 and val:  # Numeric cells (not empty)
                try:
                    num_val = float(val)
                    # Color negative values in red
                    if df.iloc[i, 0] == 'Left' and num_val < 0:
                        cell.set_text_props(color='red')
                except ValueError:
                    pass
            
            # Adjust cell height and width
            cell.set_height(0.15)
            if j == 0:
                cell.set_width(0.15)
            else:
                cell.set_width(0.12)
    
    # Title
    plt.title('Budget vs Actual Expenses', pad=20, fontsize=16)
    
    # Save to buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)
    
    return buf 