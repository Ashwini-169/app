"""
Matplotlib charts for desktop app
Industry-standard dark theme with enhanced styling
"""

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from typing import Dict, List, Union
import numpy as np
import json


# Industry-standard dark theme colors
COLORS = {
    'background': '#0F2027',
    'chart_bg': '#1A2530',
    'text_primary': '#E0E0E0',
    'text_secondary': '#B0BEC5',
    'accent_blue': '#4FC3F7',
    'accent_green': '#66BB6A',
    'accent_orange': '#FFA726',
    'accent_red': '#EF5350',
    'accent_purple': '#AB47BC',
    'grid': '#2C3E50',
}


class ChartCanvas(FigureCanvasQTAgg):
    """Base canvas for embedding Matplotlib in PyQt5 with industry styling"""
    
    def __init__(self, parent=None, width=5, height=4, dpi=110):
        # Higher DPI for sharper text
        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor=COLORS['background'])
        super().__init__(self.fig)
        self.setParent(parent)
        
        # Enable tight layout by default
        self.fig.set_tight_layout(True)


def create_pie_chart(equipment_distribution: Union[Dict[str, int], str], parent=None) -> ChartCanvas:
    """
    Equipment type distribution pie chart
    Industry-standard styling with dark theme
    """
    canvas = ChartCanvas(width=5, height=4, dpi=110)
    canvas.setParent(parent)
    ax = canvas.fig.add_subplot(111)
    
    # Parse JSON string if needed
    if isinstance(equipment_distribution, str):
        try:
            equipment_distribution = json.loads(equipment_distribution)
        except:
            equipment_distribution = {}
    
    if not equipment_distribution:
        ax.text(0.5, 0.5, 'No data available',
                ha='center', va='center', fontsize=11, color=COLORS['text_secondary'])
        ax.set_facecolor(COLORS['chart_bg'])
        canvas.draw()
        return canvas
    
    labels = list(equipment_distribution.keys())
    sizes = list(equipment_distribution.values())
    
    # Consistent color palette
    colors = [
        COLORS['accent_blue'],
        COLORS['accent_green'],
        COLORS['accent_orange'],
        COLORS['accent_red'],
        COLORS['accent_purple'],
        '#42A5F5',
        '#26A69A',
    ]
    
    # Create donut-style pie chart (industry standard)
    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=labels,
        colors=colors[:len(labels)],
        autopct='%1.1f%%',
        startangle=90,
        wedgeprops={'edgecolor': COLORS['background'], 'linewidth': 1.5},
        textprops={'color': COLORS['text_primary'], 'fontsize': 9, 'weight': '500'}
    )
    
    # Style percentage labels
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
        autotext.set_fontsize(8)
    
    ax.set_title('Equipment Type Distribution', 
                 color=COLORS['accent_blue'], 
                 fontsize=11, 
                 fontweight='600',
                 pad=10)
    ax.set_facecolor(COLORS['chart_bg'])
    
    return canvas


def create_scatter_plot(raw_data: List[Dict]) -> ChartCanvas:
    """
    Temperature vs Pressure scatter plot - CRITICAL for anomaly detection
    Industry standard: reveals operating envelope and outliers
    """
    canvas = ChartCanvas(width=6, height=4, dpi=110)
    ax = canvas.fig.add_subplot(111)
    
    if not raw_data:
        ax.text(0.5, 0.5, 'No data available',
                ha='center', va='center', fontsize=11, color=COLORS['text_secondary'])
        ax.set_facecolor(COLORS['chart_bg'])
        return canvas
    
    # Extract data
    temperatures = [float(item.get('Temperature', 0)) for item in raw_data if item.get('Temperature')]
    pressures = [float(item.get('Pressure', 0)) for item in raw_data if item.get('Pressure')]
    
    if not temperatures or not pressures:
        ax.text(0.5, 0.5, 'Insufficient data',
                ha='center', va='center', fontsize=11, color=COLORS['text_secondary'])
        ax.set_facecolor(COLORS['chart_bg'])
        return canvas
    
    # Create scatter plot with enhanced styling
    scatter = ax.scatter(
        temperatures, 
        pressures,
        alpha=0.6,
        s=50,
        c=COLORS['accent_blue'],
        edgecolors=COLORS['accent_green'],
        linewidths=0.5
    )
    
    # Add trend line (industry standard)
    if len(temperatures) > 2:
        z = np.polyfit(temperatures, pressures, 1)
        p = np.poly1d(z)
        ax.plot(
            sorted(temperatures), 
            p(sorted(temperatures)),
            "--",
            color=COLORS['accent_orange'],
            alpha=0.8,
            linewidth=2,
            label='Trend'
        )
    
    # Styling with proper contrast
    ax.set_xlabel('Temperature (°F)', color=COLORS['text_secondary'], fontsize=10, weight='500')
    ax.set_ylabel('Pressure (psi)', color=COLORS['text_secondary'], fontsize=10, weight='500')
    ax.set_title('Temperature vs Pressure Analysis', 
                 color=COLORS['accent_blue'], 
                 fontsize=11, 
                 fontweight='600',
                 pad=10)
    
    # Grid - subtle but visible
    ax.grid(True, alpha=0.15, color=COLORS['grid'], linestyle='-', linewidth=0.5)
    ax.set_facecolor(COLORS['chart_bg'])
    
    # Tick styling
    ax.tick_params(axis='both', labelcolor=COLORS['text_secondary'], labelsize=9, colors=COLORS['text_secondary'])
    
    # Legend with proper styling
    if len(temperatures) > 2:
        legend = ax.legend(
            facecolor=COLORS['chart_bg'],
            edgecolor=COLORS['accent_blue'],
            labelcolor=COLORS['text_primary'],
            framealpha=0.9,
            loc='best'
        )
    
    # Spine colors
    for spine in ax.spines.values():
        spine.set_edgecolor(COLORS['grid'])
        spine.set_linewidth(0.5)
    
    return canvas


def create_flowrate_trend(raw_data: List[Dict]) -> ChartCanvas:
    """
    Flowrate trend chart - Shows performance drift across equipment
    Industry standard: line chart for sequential comparison
    """
    canvas = ChartCanvas(width=8, height=4, dpi=110)
    ax = canvas.fig.add_subplot(111)
    
    if not raw_data:
        ax.text(0.5, 0.5, 'No data available',
                ha='center', va='center', fontsize=11, color=COLORS['text_secondary'])
        ax.set_facecolor(COLORS['chart_bg'])
        return canvas
    
    # Extract first 20 for clarity
    data = raw_data[:20]
    equipment_names = [item.get('Equipment Name', f'Eq{i+1}')[:15] for i, item in enumerate(data)]
    flowrates = [float(item.get('Flowrate', 0)) for item in data]
    
    x = np.arange(len(equipment_names))
    
    # Create area chart (filled line) - modern industry look
    ax.fill_between(x, flowrates, alpha=0.3, color=COLORS['accent_blue'])
    ax.plot(x, flowrates, 
            color=COLORS['accent_blue'], 
            linewidth=2, 
            marker='o', 
            markersize=4,
            markerfacecolor=COLORS['accent_green'],
            markeredgecolor='white',
            markeredgewidth=0.5)
    
    # Add average line (industry baseline)
    avg_flowrate = np.mean(flowrates)
    ax.axhline(y=avg_flowrate, 
               color=COLORS['accent_orange'], 
               linestyle='--', 
               linewidth=1.5, 
               alpha=0.7,
               label=f'Average: {avg_flowrate:.2f}')
    
    # Styling
    ax.set_xlabel('Equipment', color=COLORS['text_secondary'], fontsize=10, weight='500')
    ax.set_ylabel('Flowrate (L/min)', color=COLORS['text_secondary'], fontsize=10, weight='500')
    ax.set_title('Flowrate Performance Trend (First 20)', 
                 color=COLORS['accent_blue'], 
                 fontsize=11, 
                 fontweight='600',
                 pad=10)
    
    ax.set_xticks(x)
    ax.set_xticklabels(equipment_names, rotation=45, ha='right', fontsize=8, color=COLORS['text_secondary'])
    ax.tick_params(axis='y', labelcolor=COLORS['text_secondary'], labelsize=9, colors=COLORS['text_secondary'])
    
    # Grid - horizontal only (cleaner for trends)
    ax.grid(True, alpha=0.15, color=COLORS['grid'], linestyle='-', linewidth=0.5, axis='y')
    ax.set_facecolor(COLORS['chart_bg'])
    
    # Legend
    legend = ax.legend(
        facecolor=COLORS['chart_bg'],
        edgecolor=COLORS['accent_blue'],
        labelcolor=COLORS['text_primary'],
        framealpha=0.9,
        loc='upper right'
    )
    
    # Spine colors
    for spine in ax.spines.values():
        spine.set_edgecolor(COLORS['grid'])
        spine.set_linewidth(0.5)
    
    return canvas


def create_bar_chart(raw_data: List[Dict]) -> ChartCanvas:
    """
    Parameter comparison bar chart - Multi-parameter view
    Industry standard: grouped bars for comparison
    """
    canvas = ChartCanvas(width=8, height=4, dpi=110)
    ax = canvas.fig.add_subplot(111)
    
    if not raw_data:
        ax.text(0.5, 0.5, 'No data available',
                ha='center', va='center', fontsize=11, color=COLORS['text_secondary'])
        ax.set_facecolor(COLORS['chart_bg'])
        return canvas
    
    # Extract first 15 items for clarity (industry practice)
    data = raw_data[:15]
    equipment_names = [item.get('Equipment Name', f'Eq{i+1}')[:12] for i, item in enumerate(data)]
    flowrates = [float(item.get('Flowrate', 0)) for item in data]
    pressures = [float(item.get('Pressure', 0)) for item in data]
    temperatures = [float(item.get('Temperature', 0)) for item in data]
    
    x = np.arange(len(equipment_names))
    width = 0.25
    
    # Create grouped bars with proper spacing
    bars1 = ax.bar(x - width, flowrates, width, 
                   label='Flowrate', 
                   color=COLORS['accent_blue'], 
                   alpha=0.85,
                   edgecolor=COLORS['background'],
                   linewidth=0.5)
    bars2 = ax.bar(x, pressures, width, 
                   label='Pressure', 
                   color=COLORS['accent_green'], 
                   alpha=0.85,
                   edgecolor=COLORS['background'],
                   linewidth=0.5)
    bars3 = ax.bar(x + width, temperatures, width, 
                   label='Temperature', 
                   color=COLORS['accent_orange'], 
                   alpha=0.85,
                   edgecolor=COLORS['background'],
                   linewidth=0.5)
    
    # Styling
    ax.set_xlabel('Equipment', color=COLORS['text_secondary'], fontsize=10, weight='500')
    ax.set_ylabel('Values', color=COLORS['text_secondary'], fontsize=10, weight='500')
    ax.set_title('Multi-Parameter Comparison', 
                 color=COLORS['accent_blue'], 
                 fontsize=11, 
                 fontweight='600',
                 pad=10)
    
    ax.set_xticks(x)
    ax.set_xticklabels(equipment_names, rotation=45, ha='right', fontsize=8, color=COLORS['text_secondary'])
    ax.tick_params(axis='y', labelcolor=COLORS['text_secondary'], labelsize=9, colors=COLORS['text_secondary'])
    
    # Legend with proper styling
    legend = ax.legend(
        facecolor=COLORS['chart_bg'],
        edgecolor=COLORS['accent_blue'],
        labelcolor=COLORS['text_primary'],
        framealpha=0.9,
        loc='upper right',
        ncol=3
    )
    
    # Grid - horizontal only
    ax.grid(True, alpha=0.15, color=COLORS['grid'], linestyle='-', linewidth=0.5, axis='y')
    ax.set_facecolor(COLORS['chart_bg'])
    
    # Spine colors
    for spine in ax.spines.values():
        spine.set_edgecolor(COLORS['grid'])
        spine.set_linewidth(0.5)
    
    return canvas


def create_summary_bar_chart(avg_flowrate: float, avg_pressure: float, avg_temperature: float) -> ChartCanvas:
    """
    Create simple bar chart showing averages
    """
    canvas = ChartCanvas(width=5, height=3)
    ax = canvas.fig.add_subplot(111)
    
    categories = ['Avg Flowrate', 'Avg Pressure', 'Avg Temperature']
    values = [avg_flowrate, avg_pressure, avg_temperature]
    colors = ['#4FC3F7', '#66BB6A', '#FFA726']
    
    bars = ax.bar(categories, values, color=colors, alpha=0.8)
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.2f}',
                ha='center', va='bottom', color='#E0E0E0', fontsize=9)
    
    ax.set_ylabel('Value', color='#B0BEC5', fontsize=10)
    ax.set_title('Average Parameters', color='#4FC3F7', fontsize=12, pad=15)
    ax.tick_params(axis='x', labelcolor='#B0BEC5', labelsize=8)
    ax.tick_params(axis='y', labelcolor='#B0BEC5')
    ax.grid(True, alpha=0.2, color='#4FC3F7', axis='y')
    ax.set_facecolor('#1E293B')
    
    canvas.fig.tight_layout()
    return canvas
