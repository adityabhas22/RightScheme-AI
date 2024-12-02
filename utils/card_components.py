import streamlit as st
from typing import Optional

def create_card(title: str, content: str, icon: str = "", is_clickable: bool = False):
    """Create a styled card component."""
    card_html = f"""
        <div class='stCard' {'style="cursor: pointer;"' if is_clickable else ''}>
            <h3 style='margin-bottom: 1rem;'>{icon} {title}</h3>
            <p style='color: #666;'>{content}</p>
        </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

def create_feature_card(title: str, description: str, icon: str, action_label: str, page_path: str):
    """Create a feature card with action button."""
    st.info(f"### {icon} {title}")
    st.write(description)
    if st.button(action_label, use_container_width=True):
        st.switch_page(page_path)