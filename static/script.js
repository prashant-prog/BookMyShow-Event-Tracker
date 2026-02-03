//This Project is Created By Prashant Sharma
document.addEventListener('DOMContentLoaded', () => {
    const fetchBtn = document.getElementById('fetch-btn');
    const citySelect = document.getElementById('city-select');
    const statusContainer = document.getElementById('status-container');
    const statusMessage = document.getElementById('status-message');
    const btnText = document.getElementById('btn-text');
    const btnSpinner = document.getElementById('btn-spinner');

    fetchBtn.addEventListener('click', async () => {
        // 1. UI Loading State
        setLoadingState(true);
        hideStatus();

        try {
            // 2. Prepare Payload (in case we add city selection logic later)
            const selectedCity = citySelect.value;

            // 3. Call Backend
            // Note: In a real app, we might send { city: selectedCity }
            const response = await fetch('/run-scraper', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ city: selectedCity })
            });

            const data = await response.json();

            // 4. Handle Response
            if (response.ok && data.status === 'success') {
                showStatus(data.message, 'success');
            } else {
                showStatus(data.message || 'An unknown error occurred.', 'error');
            }

        } catch (error) {
            console.error('Network Error:', error);
            showStatus('Failed to connect to server. Is the backend running?', 'error');
        } finally {
            // 5. Reset UI State
            setLoadingState(false);
        }
    });

    function setLoadingState(isLoading) {
        if (isLoading) {
            fetchBtn.disabled = true;
            btnText.textContent = 'Processing...';
            btnSpinner.classList.remove('hidden');
        } else {
            fetchBtn.disabled = false;
            btnText.textContent = 'Fetch / Update Events';
            btnSpinner.classList.add('hidden');
        }
    }

    function showStatus(message, type) {
        statusContainer.classList.remove('hidden', 'success', 'error');
        statusContainer.classList.add(type);
        statusMessage.textContent = message;
    }

    function hideStatus() {
        statusContainer.classList.add('hidden');
    }
});
