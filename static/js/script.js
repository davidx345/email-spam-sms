// static/js/script.js
document.addEventListener('DOMContentLoaded', function() {
    // --- DOM Elements ---
    const messageInput = document.getElementById('message-input');
    const checkButton = document.getElementById('check-button');
    const singleResultSection = document.getElementById('single-result-section');

    const batchMessageInput = document.getElementById('batch-message-input');
    const batchCheckTextButton = document.getElementById('batch-check-text-button');
    const batchFileInput = document.getElementById('batch-file-input');
    const batchCheckFileButton = document.getElementById('batch-check-file-button');
    const batchResultsSection = document.getElementById('batch-results-section');

    const errorAlertContainer = document.getElementById('error-alert-container');
    const currentDateEl = document.getElementById('current-date');

    // --- Utility Functions ---
    function showLoading(button, show = true) {
        const spinner = button.querySelector('.spinner-border');
        if (show) {
            button.disabled = true;
            if(spinner) spinner.classList.remove('d-none');
            // Keep original text if spinner is separate, or change text
            // button.dataset.originalText = button.textContent;
            // button.textContent = 'Processing...'; // If no dedicated spinner text area
        } else {
            button.disabled = false;
            if(spinner) spinner.classList.add('d-none');
            // if (button.dataset.originalText) button.textContent = button.dataset.originalText;
        }
    }

    function displayError(message, type = 'error') {
        errorAlertContainer.innerHTML = ''; // Clear previous errors
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-custom ${type === 'error' ? 'alert-custom-error' : 'alert-custom-success'} alert-dismissible fade show`;
        alertDiv.role = 'alert';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                <span aria-hidden="true">&times;</span>
            </button>
        `;
        errorAlertContainer.appendChild(alertDiv);
    }

    function createResultCard(resultData, index = 0, isBatch = false) {
        const cardId = `result-${isBatch ? 'batch-' : 'single-'}${index}`;
        const card = document.createElement('div');
        card.className = 'result-card card shadow-sm mb-3';
        card.id = cardId;

        const isSpam = resultData.is_spam;
        const predictionText = resultData.prediction; // "Spam" or "Not Spam"
        const spamProbability = parseFloat(resultData.spam_probability).toFixed(2);
        const hamProbability = parseFloat(resultData.ham_probability).toFixed(2);

        let headerClass = isSpam ? 'spam' : 'not-spam';
        let headerText = isSpam ? 'Spam Detected' : 'Not Spam';

        card.innerHTML = `
            <div class="result-header card-header ${headerClass}">
                <h5 class="mb-0">${headerText}</h5>
            </div>
            <div class="card-body result-details">
                ${isBatch ? `<p class=\"text-muted small\"><em>Message: ${escapeHTML(resultData.text.substring(0,100))}${resultData.text.length > 100 ? '...' : ''}</em></p>` : ''}
                <div class="probability-section mb-2">
                    <p class="mb-1">Confidence:</p>
                    <div class="progress">
                        <div class="progress-bar ${isSpam ? 'bg-danger' : 'bg-success'}" role="progressbar" style="width: ${isSpam ? spamProbability : hamProbability}%;" aria-valuenow="${isSpam ? spamProbability : hamProbability}" aria-valuemin="0" aria-valuemax="100">
                            ${isSpam ? spamProbability : hamProbability}%
                        </div>
                    </div>
                    <p class="small text-muted">
                        Spam: <span class="font-weight-bold">${spamProbability}%</span> | 
                        Not Spam: <span class="font-weight-bold">${hamProbability}%</span>
                    </p>
                </div>
                <div class="feedback-buttons">
                    <small class="mr-2">Was this prediction correct?</small>
                    <button class="btn btn-sm btn-outline-success feedback-btn" data-message="${escapeHTML(resultData.text)}" data-predicted="${predictionText}" data-feedback="correct">Yes</button>
                    <button class="btn btn-sm btn-outline-danger feedback-btn" data-message="${escapeHTML(resultData.text)}" data-predicted="${predictionText}" data-feedback="incorrect">No</button>
                </div>
            </div>
        `;
        return card;
    }

    function escapeHTML(str) {
        if (typeof str !== 'string') return str;
        return str.replace(/[&<>"]/g, function (tag) {
            const chars = {
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
            };
            return chars[tag] || tag;
        });
    }

    // --- Event Handlers ---
    async function handleSinglePrediction() {
        const message = messageInput.value.trim();
        if (!message) {
            displayError('Please enter a message to check.');
            return;
        }
        showLoading(checkButton);
        singleResultSection.innerHTML = ''; // Clear previous single result
        errorAlertContainer.innerHTML = ''; // Clear previous errors

        try {
            const response = await fetch('/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message }),
            });
            const result = await response.json();
            if (!response.ok) {
                throw new Error(result.error || 'Failed to get prediction');
            }
            const resultCard = createResultCard(result);
            singleResultSection.appendChild(resultCard);
        } catch (error) {
            console.error('Single Prediction Error:', error);
            displayError(`Error: ${error.message}`);
        } finally {
            showLoading(checkButton, false);
        }
    }

    async function handleBatchPrediction(source) { // source can be 'text' or 'file'
        let payload;
        let buttonToLoad;

        errorAlertContainer.innerHTML = ''; // Clear previous errors
        batchResultsSection.innerHTML = ''; // Clear previous batch results

        if (source === 'text') {
            const messagesText = batchMessageInput.value.trim();
            if (!messagesText) {
                displayError('Please enter messages for batch prediction.');
                return;
            }
            payload = new FormData();
            payload.append('messages_text', messagesText);
            buttonToLoad = batchCheckTextButton;
        } else { // source === 'file'
            const file = batchFileInput.files[0];
            if (!file) {
                displayError('Please select a file for batch prediction.');
                return;
            }
            payload = new FormData();
            payload.append('file', file);
            buttonToLoad = batchCheckFileButton;
        }

        showLoading(buttonToLoad);

        try {
            const response = await fetch('/predict_batch', {
                method: 'POST',
                body: payload, // FormData is sent as multipart/form-data
            });
            const results = await response.json();
            if (!response.ok) {
                throw new Error(results.error || 'Failed to get batch prediction');
            }

            if (results && results.length > 0) {
                const table = document.createElement('table');
                table.className = 'table table-striped table-hover mt-3';
                table.id = 'batch-results-table';
                table.innerHTML = `
                    <thead class="thead-light">
                        <tr>
                            <th>#</th>
                            <th>Message (Preview)</th>
                            <th>Prediction</th>
                            <th>Spam Probability</th>
                            <th>Feedback</th>
                        </tr>
                    </thead>
                    <tbody>
                    </tbody>
                `;
                const tbody = table.querySelector('tbody');
                results.forEach((result, index) => {
                    const tr = tbody.insertRow();
                    const isSpam = result.is_spam;
                    const predictionText = result.prediction;

                    tr.innerHTML = `
                        <td>${index + 1}</td>
                        <td>${escapeHTML(result.text.substring(0, 70))}${result.text.length > 70 ? '...' : ''}</td>
                        <td class="${isSpam ? 'text-danger' : 'text-success'}">${predictionText}</td>
                        <td>${parseFloat(result.spam_probability).toFixed(2)}%</td>
                        <td>
                            <button class="btn btn-sm btn-outline-success feedback-btn" title="Correct" data-message="${escapeHTML(result.text)}" data-predicted="${predictionText}" data-feedback="correct"><small>Yes</small></button>
                            <button class="btn btn-sm btn-outline-danger feedback-btn" title="Incorrect" data-message="${escapeHTML(result.text)}" data-predicted="${predictionText}" data-feedback="incorrect"><small>No</small></button>
                        </td>
                    `;
                });
                batchResultsSection.appendChild(table);
            } else {
                displayError('No results returned from batch prediction.', 'info');
            }

        } catch (error) {
            console.error('Batch Prediction Error:', error);
            displayError(`Batch Error: ${error.message}`);
        } finally {
            showLoading(buttonToLoad, false);
        }
    }

    async function handleFeedback(event) {
        if (!event.target.classList.contains('feedback-btn')) return;

        const button = event.target;
        const message = button.dataset.message;
        const predictedLabel = button.dataset.predicted; // "Spam" or "Not Spam"
        const feedbackType = button.dataset.feedback; // "correct" or "incorrect"

        let actualLabel;
        if (feedbackType === 'correct') {
            actualLabel = (predictedLabel === 'Spam') ? 'spam' : 'ham';
        } else { // incorrect
            actualLabel = (predictedLabel === 'Spam') ? 'ham' : 'spam';
        }

        // Disable buttons to prevent multiple clicks
        const feedbackButtons = button.parentElement.querySelectorAll('.feedback-btn');
        feedbackButtons.forEach(btn => btn.disabled = true);

        try {
            const response = await fetch('/feedback', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message, predicted_label: predictedLabel, actual_label: actualLabel }),
            });
            const result = await response.json();
            if (!response.ok) {
                throw new Error(result.error || 'Failed to submit feedback');
            }
            // Visually indicate success by replacing the content of the button's parent element
            if (button.parentElement) {
                button.parentElement.innerHTML = '<small class="text-success"><em>Feedback sent! Thank you.</em></small>';
            }
            // displayError('Feedback submitted successfully!', 'success'); // Alternative: use the main alert area
        } catch (error) {
            console.error('Feedback Error:', error);
            displayError(`Feedback Error: ${error.message}`);
            // Re-enable buttons if error
            feedbackButtons.forEach(btn => btn.disabled = false);
        }
    }

    // --- Event Listeners ---
    if (checkButton) {
        checkButton.addEventListener('click', handleSinglePrediction);
    }
    if (batchCheckTextButton) {
        batchCheckTextButton.addEventListener('click', () => handleBatchPrediction('text'));
    }
    if (batchCheckFileButton) {
        batchCheckFileButton.addEventListener('click', () => handleBatchPrediction('file'));
    }

    // Delegated event listener for feedback buttons (works for dynamically added elements)
    document.body.addEventListener('click', handleFeedback);

    // Set current date in footer
    if (currentDateEl) {
        const today = new Date();
        const options = { year: 'numeric', month: 'long', day: 'numeric' };
        currentDateEl.textContent = today.toLocaleDateString(undefined, options);
    }
});