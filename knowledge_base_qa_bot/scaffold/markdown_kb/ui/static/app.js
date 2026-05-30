document.addEventListener("DOMContentLoaded", () => {
    // DOM Element selections
    const btnIndex = document.getElementById("btn-index");
    const btnIndexText = document.getElementById("btn-index-text");
    const indexSpinner = document.getElementById("index-spinner");
    const indexMetrics = document.getElementById("index-metrics");
    const metricFiles = document.getElementById("metric-files");
    const metricSections = document.getElementById("metric-sections");
    const statusPulse = document.getElementById("status-pulse");
    const statusText = document.getElementById("status-text");
    
    const chatForm = document.getElementById("chat-form");
    const chatInput = document.getElementById("chat-input");
    const chatHistory = document.getElementById("chat-history");
    const sourcesList = document.getElementById("sources-list");
    const sampleQueries = document.getElementById("sample-queries");

    // Check Index status on boot
    checkIndexStatus();

    // Handle Click on Sample Queries
    sampleQueries.addEventListener("click", (e) => {
        const chip = e.target.closest(".query-chip");
        if (!chip) return;
        chatInput.value = chip.getAttribute("data-query");
        chatForm.dispatchEvent(new Event("submit"));
    });

    // 1. Handle Indexing Rebuild button click
    btnIndex.addEventListener("click", async () => {
        setIndexingState(true);
        try {
            const response = await fetch("/index", { method: "POST" });
            if (!response.ok) throw new Error("Index request failed");
            
            const data = await response.json();
            
            // Update stats
            metricFiles.textContent = data.files_indexed;
            metricSections.textContent = data.sections_indexed;
            indexMetrics.style.display = "flex";
            
            // Set badge to active (Green)
            updateStatusBadge(true, `Index Status: Active (${data.sections_indexed} Sections)`);
            
            // Show sample queries
            sampleQueries.style.display = "flex";
            
            appendBotMessage("Success! The search index has been rebuilt successfully. You can now chat with me!");
        } catch (error) {
            console.error(error);
            appendBotMessage("An error occurred while building the index. Please make sure your server is running.");
        } finally {
            setIndexingState(false);
        }
    });

    // 2. Handle Chat Form Submit
    chatForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const query = chatInput.value.trim();
        if (!query) return;
        
        chatInput.value = "";
        
        // Render user message bubble
        appendUserMessage(query);
        
        // Render bot loading skeleton bubble
        const skeletonId = appendLoadingSkeleton();
        
        try {
            const response = await fetch("/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ query })
            });
            
            if (!response.ok) throw new Error("Chat request failed");
            const data = await response.json();
            
            // Remove the loading skeleton
            removeLoadingSkeleton(skeletonId);
            
            // Render the real answer (with formatted clickable citations)
            appendBotMessage(data.answer, data.sources);
            
            // Render the source citations cards in the sidebar
            renderSources(data.sources);
        } catch (error) {
            console.error(error);
            removeLoadingSkeleton(skeletonId);
            appendBotMessage("An error occurred while calling the Q&A bot. Please make sure your server and Gemini API keys are configured.");
        }
    });

    /* ==========================================================================
       Helper / UI Rendering Functions
       ========================================================================== */
       
    // Check if the KB is already indexed on server startup
    async function checkIndexStatus() {
        try {
            const response = await fetch("/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ query: "status_check_dummy_string" })
            });
            const data = await response.json();
            
            // If the server says it's not indexed, keep status unindexed
            if (data.answer && data.answer.includes("not been indexed yet")) {
                updateStatusBadge(false, "Index Status: Unindexed");
                sampleQueries.style.display = "none";
            } else {
                updateStatusBadge(true, "Index Status: Active");
                sampleQueries.style.display = "flex";
            }
        } catch (e) {
            updateStatusBadge(false, "Index Status: Offline");
            sampleQueries.style.display = "none";
        }
    }

    function setIndexingState(isLoading) {
        btnIndex.disabled = isLoading;
        if (isLoading) {
            btnIndexText.textContent = "Indexing...";
            indexSpinner.style.display = "inline-block";
        } else {
            btnIndexText.textContent = "Rebuild Search Index";
            indexSpinner.style.display = "none";
        }
    }

    function updateStatusBadge(isActive, text) {
        statusText.textContent = text;
        if (isActive) {
            statusPulse.className = "pulse-indicator green";
        } else {
            statusPulse.className = "pulse-indicator red";
        }
    }

    function appendUserMessage(text) {
        const msg = document.createElement("div");
        msg.className = "chat-message user-message";
        msg.textContent = text;
        chatHistory.appendChild(msg);
        scrollToBottom();
    }

    function appendBotMessage(text, sources = []) {
        const msg = document.createElement("div");
        msg.className = "chat-message bot-message";
        
        // Regex to parse citations [filename.md#heading-slug]
        const citationRegex = /\[([a-zA-Z0-9_\-\.]+?\.md)#([a-zA-Z0-9_\-\.]+?)\]/g;
        
        // Convert plain citations to clickable HTML pills
        const htmlContent = text.replace(citationRegex, (match, filename, slug) => {
            const sourceId = `${filename}#${slug}`;
            return `<span class="citation-tag" onclick="highlightSource('${sourceId}')">${match}</span>`;
        });
        
        msg.innerHTML = htmlContent;
        chatHistory.appendChild(msg);
        scrollToBottom();
    }

    function appendLoadingSkeleton() {
        const skeletonId = "skeleton-" + Date.now();
        const msg = document.createElement("div");
        msg.className = "chat-message bot-message loading-skeleton";
        msg.id = skeletonId;
        msg.innerHTML = `
            <div class="skeleton-line" style="width: 80%"></div>
            <div class="skeleton-line" style="width: 95%"></div>
            <div class="skeleton-line" style="width: 60%"></div>
        `;
        chatHistory.appendChild(msg);
        scrollToBottom();
        return skeletonId;
    }

    function removeLoadingSkeleton(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }

    function renderSources(sources) {
        sourcesList.innerHTML = "";
        
        if (!sources || sources.length === 0) {
            sourcesList.innerHTML = `<div class="empty-sources">No sources cited for this response.</div>`;
            return;
        }
        
        sources.forEach(src => {
            const item = document.createElement("div");
            item.className = "source-item";
            item.id = `card-${src.source}`; // ID to anchor highlight interactions!
            
            item.innerHTML = `
                <div class="source-meta">
                    <span class="source-id">${src.source}</span>
                    <span class="source-score">BM25: ${src.score}</span>
                </div>
                <div class="source-heading">${src.heading}</div>
                <div class="source-snippet">${escapeHtml(src.content)}</div>
            `;
            
            sourcesList.appendChild(item);
        });
    }

    function scrollToBottom() {
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    function escapeHtml(str) {
        return str
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
});

// Global interaction handler (called from dynamically inserted onclick attributes in citation HTML)
function highlightSource(sourceId) {
    const card = document.getElementById(`card-${sourceId}`);
    if (card) {
        // Scroll the matching source card into view inside the sidebar container
        card.scrollIntoView({ behavior: "smooth", block: "nearest" });
        
        // Add highlighted glow class
        card.classList.add("highlighted");
        
        // Automatically remove the glow after 3 seconds
        setTimeout(() => {
            card.classList.remove("highlighted");
        }, 3000);
    }
}
