import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Flowchart Viewer",   # Title in browser tab
    page_icon="📊",                  # Emoji or path to icon
    layout="wide",                   # Options: "centered" (default) or "wide"
    initial_sidebar_state="expanded" # Options: "auto", "expanded", "collapsed"
)

st.title("📊 Methodology (Flow Chart)")

# Path to your SVG file
svg_file = ".\\resources\\Flowchart.svg"

# Read the SVG content
with open(svg_file, "r", encoding="utf-8") as f:
    svg_content = f.read()

# Wrap the SVG in a responsive container
html_code = f"""
<div style="
    width: 100%;
    height: 100%;        /* Full viewport height */
    overflow: auto;       /* Scrollbars if SVG too large */
">
    {svg_content}
</div>
"""

# Render the SVG in Streamlit
components.html(html_code, height=800, scrolling=True)