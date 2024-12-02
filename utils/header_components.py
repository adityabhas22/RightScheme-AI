import streamlit as st

def display_header(title: str, subtitle: str = "", icon: str = ""):
    """Display a styled header with optional subtitle and icon."""
    st.markdown(f"""
        <div style='text-align: center; padding: 2rem 0;'>
            <h1 style='font-size: 2.5rem; margin-bottom: 0.5rem;'>{icon} {title}</h1>
            <p style='font-size: 1.2rem; color: #666;'>{subtitle}</p>
        </div>
    """, unsafe_allow_html=True)

def create_progress_indicator(current: int, total: int, label: str = "Progress"):
    """Create a styled progress indicator."""
    progress = current / total
    st.markdown(f"### {label}")
    st.progress(progress)
    st.caption(f"{current} of {total} completed")