# Walkthrough: Premium Web UI Package with Interactive Sample Queries

We have successfully built and integrated a state-of-the-art Single-Page Web Dashboard served directly by the FastAPI server! The front-end code is cleanly organized into a self-contained Python package (`ui/`), isolating it from your core API logic.

---

## 📁 Changes Implemented

We created a self-contained `ui` Python package with the following modules and assets:

1. **`ui/__init__.py`**: Designation file making `ui/` an importable Python package.
2. **`ui/routes.py`**: APIRouter that handles routing for the HTML template.
3. **`app/main.py`**: Integrated the `ui_router` and mounted `/ui/static` to dynamically serve the asset directory.
4. **`ui/static/index.html`**: Structured dashboard featuring header status badges, a search index controller card, an interactive chat terminal (with interactive sample queries floating above the input bar), and a sources inspector list.
5. **`ui/static/style.css`**: Deep dark theme (using tailored HSL palettes) complete with glassmorphic elements, neon glow pulsing indicators, customized scrollbars, glass chips, and keyframe slide-in message animations.
6. **`ui/static/app.js`**: Drives the interactive client application. It:
   - Automatically checks server index status on startup.
   - Automatically shows or hides the sample query chips depending on whether the index is active.
   - Handles clicking on sample query chips to auto-fill the chat input and auto-submit the form.
   - Handles async rebuilding and chat query requests.
   - Displays skeleton loaders while fetching answers from Gemini 2.5 Flash.
   - Parses inline citations to create clickable citation pills that trigger smooth-scrolling and neon highlighting focus on corresponding source cards in the sidebar!

---

## 🚀 How to Use the UI Dashboard

Follow these steps to run and experience your new premium dashboard:

### 1. Boot up the Server
In your terminal, navigate to your project directory and run:
```bash
# 1. Set your Gemini API key
export GOOGLE_API_KEY="your-gemini-api-key-here"

# 2. Go to the markdown_kb folder
cd scaffold/markdown_kb

# 3. Spin up the server
.venv/bin/uvicorn app.main:app --reload
```

### 2. Open the Dashboard
Open your browser and navigate to:
`http://localhost:8000/`

### 3. Experience the Features
- **Rebuild Index:** Click the **"Rebuild Search Index"** button. Watch the loading spinner animate and the metrics panel dynamically pop up showing that `4 Files` and `20 Sections` have been indexed on your disk! The status badge in the header will pulse green and turn to **"Active"**.
- **Sample Query Chips:** As soon as the index is active, beautiful interactive sample query chips will float above the input bar (e.g. `"How long do refunds take?"`). Click any of these chips to automatically fill the query into the chat bar and execute it!
- **Submit Queries:** Ask custom grounded questions in the chat bar. You'll see a loading skeleton flash, and then a grounded answer will slide in citing the source files.
- **Inspect Sources:** Watch the right-side **Source Inspector** panel dynamically populate with cards showing the exact ranked sections from your markdown docs along with their raw content and BM25 scores!
- **Citation Glow Highlight:** Click on any of the purple citation tags (like `[refund_policy.md#refund-timeline]`) inside the chat bubbles. The right-side sources panel will **smoothly scroll directly to that specific card and highlight it with a brilliant neon purple pulse!**
