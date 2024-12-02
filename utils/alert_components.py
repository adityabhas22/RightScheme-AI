import streamlit as st
from typing import Literal

AlertType = Literal["info", "success", "warning", "error"]

def get_alert_color(type: AlertType) -> str:
    """Get the background color for different alert types."""
    colors = {
        "info": "#e3f2fd",
        "success": "#e8f5e9",
        "warning": "#fff3e0",
        "error": "#ffebee"
    }
    return colors.get(type, "#e3f2fd")

def create_alert(message: str, type: AlertType = "info"):
    """Create a styled alert message."""
    alert_types = {
        "info": "💡",
        "success": "✅",
        "warning": "⚠️",
        "error": "❌"
    }
    icon = alert_types.get(type, "💡")
    st.markdown(f"""
        <div style='padding: 1rem; border-radius: 0.5rem; background-color: {get_alert_color(type)};'>
            {icon} {message}
        </div>
    """, unsafe_allow_html=True)