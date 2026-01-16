import streamlit as st
import base64
from io import BytesIO

def inject_premium_styles():
    """Inject glassmorphism and viewer CSS."""
    st.markdown("""
    <style>
        .viewer-container {
            border-radius: 15px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            overflow: auto;
            max-height: 80vh;
            display: flex;
            justify-content: center;
            align-items: flex-start;
            padding: 5px;
            cursor: grab;
        }
        .viewer-container:active {
            cursor: grabbing;
        }
        .viewer-image {
            transition: width 0.3s ease;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        }
    </style>
    """, unsafe_allow_html=True)

def interactive_viewer(image, zoom_percent: int):
    """Render the premium interactive image viewer with zoom and pan."""
    if not image:
        return
    
    # Get base64
    buffered = BytesIO()
    image.save(buffered, format="JPEG", quality=85)
    img_b64 = base64.b64encode(buffered.getvalue()).decode()
    
    st.markdown(f"""
    <div class="viewer-container" id="viewer" onmousedown="startDragging(event)" onmousemove="drag(event)" onmouseup="stopDragging()" onmouseleave="stopDragging()">
        <img src="data:image/jpeg;base64,{img_b64}" 
             class="viewer-image" 
             id="zoomable-img"
             style="width: {zoom_percent}%;">
    </div>
    
    <script>
        let isDragging = false;
        let startX, startY, scrollLeft, scrollTop;
        const viewer = document.getElementById('viewer');

        function startDragging(e) {{
            isDragging = true;
            startX = e.pageX - viewer.offsetLeft;
            startY = e.pageY - viewer.offsetTop;
            scrollLeft = viewer.scrollLeft;
            scrollTop = viewer.scrollTop;
        }}

        function stopDragging() {{
            isDragging = false;
        }}

        function drag(e) {{
            if (!isDragging) return;
            e.preventDefault();
            const x = e.pageX - viewer.offsetLeft;
            const y = e.pageY - viewer.offsetTop;
            const walkX = (x - startX) * 2;
            const walkY = (y - startY) * 2;
            viewer.scrollLeft = scrollLeft - walkX;
            viewer.scrollTop = scrollTop - walkY;
        }}
    </script>
    """, unsafe_allow_html=True)
