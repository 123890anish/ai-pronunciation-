/**
 * Dashboard live status updater.
 */
document.addEventListener("DOMContentLoaded", () => {
    // Optional periodic health check for Ollama daemon
    async function checkHealth() {
        try {
            const resp = await fetch("/assessments/api/health/");
            if (resp.ok) {
                const data = await resp.json();
                console.log("LLM Service Status:", data);
            }
        } catch (e) {
            console.debug("Health check inactive:", e);
        }
    }
    checkHealth();
});
