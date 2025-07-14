document.addEventListener('DOMContentLoaded', () => {
    const walletAddressInput = document.getElementById('walletAddress');
    const verifyButton = document.getElementById('verifyButton');
    const resultsArea = document.getElementById('resultsArea');
    const loadingIndicator = document.getElementById('loadingIndicator');

    verifyButton.addEventListener('click', async () => {
        const address = walletAddressInput.value.trim();

        if (!address) {
            resultsArea.innerHTML = '<p style="color: #ff7979;">Please enter a wallet address.</p>';
            return;
        }

        loadingIndicator.style.display = 'block';
        resultsArea.innerHTML = ''; // Clear previous results

        try {
            // Adjust the URL if your FastAPI app is running on a different port or domain
            // For local development where FastAPI serves this static file, /verify/ should work.
            const response = await fetch(`/verify/${encodeURIComponent(address)}`);

            if (!response.ok) {
                let errorDetail = "Failed to fetch data.";
                try {
                    const errorData = await response.json();
                    errorDetail = errorData.detail || `HTTP error! Status: ${response.status}`;
                } catch (e) {
                    // If parsing error JSON fails, use the status text or default message
                    errorDetail = `HTTP error! Status: ${response.status} - ${response.statusText}`;
                }
                throw new Error(errorDetail);
            }

            const data = await response.json();
            displayResults(data);

        } catch (error) {
            resultsArea.innerHTML = `<p style="color: #ff7979;">Error: ${error.message}</p>`;
            console.error('Verification error:', error);
        } finally {
            loadingIndicator.style.display = 'none';
        }
    });

    function displayResults(data) {
        resultsArea.innerHTML = ''; // Clear previous results or loading message

        const resultCard = document.createElement('div');
        resultCard.className = 'result-item';

        let content = `<h3>Verification Results for: ${escapeHTML(data.address)}</h3>`;

        content += `<p><span class="label">Sanctioned by Local Blacklist:</span> <span class="value-${data.sanctioned_by_local_blacklist}">${data.sanctioned_by_local_blacklist}</span></p>`;
        content += `<p><span class="label">On Polkadot Scam List:</span> <span class="value-${data.on_polkadot_scam_list}">${data.on_polkadot_scam_list}</span></p>`;

        content += `<p><span class="label">Risk Level:</span> <span class="risk-${data.risk_level.toLowerCase()}">${escapeHTML(data.risk_level)}</span></p>`;
        content += `<p><span class="label">Risk Score:</span> ${data.risk_score}/100</p>`;

        if (data.graphsense_tags && data.graphsense_tags.length > 0) {
            if (typeof data.graphsense_tags[0] === 'string' && data.graphsense_tags[0].startsWith("GraphSense API")) {
                content += `<p><span class="label">GraphSense Info:</span> ${escapeHTML(data.graphsense_tags[0])}</p>`;
            } else {
                content += `<p><span class="label">GraphSense Tags:</span></p><ul>`;
                data.graphsense_tags.forEach(tag => {
                    if (typeof tag === 'object' && tag !== null && tag.label) {
                        content += `<li>${escapeHTML(tag.label)} (Source: ${escapeHTML(tag.source || 'N/A')}, Category: ${escapeHTML(tag.category || 'N/A')})</li>`;
                    } else {
                        content += `<li>${escapeHTML(JSON.stringify(tag))}</li>`;
                    }
                });
                content += `</ul>`;
            }
        } else {
            content += `<p><span class="label">GraphSense Tags:</span> No tags found or API not responsive.</p>`;
        }

        resultCard.innerHTML = content;
        resultsArea.appendChild(resultCard);
    }

    // Helper function to escape HTML characters to prevent XSS
    function escapeHTML(str) {
        if (typeof str !== 'string') return str; // Return non-strings as is
        return str.replace(/[&<>"']/g, function (match) {
            return {
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#39;'
            }[match];
        });
    }
});
