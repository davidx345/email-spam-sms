// static/js/script.js
document.addEventListener('DOMContentLoaded', function() {
    const messageInput = document.getElementById('message-input');
    const checkButton = document.getElementById('check-button');
    const resultCard = document.getElementById('result-card');
    const resultHeader = document.getElementById('result-header');
    const resultTitle = document.getElementById('result-title');
    const probabilityBar = document.getElementById('probability-bar');
    const probabilityValue = document.getElementById('probability-value');

    checkButton.addEventListener('click', async function() {
        const message = messageInput.value.trim();
        
        if (!message) {
            alert('Please enter a message to check.');
            return;
        }
        
        // Show loading state
        checkButton.disabled = true;
        checkButton.textContent = 'Checking...';
        
        try {
            // Send message to API
            const response = await fetch('/predict', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message }),
            });
            
            if (!response.ok) {
                throw new Error('Failed to get prediction');
            }
            
            const result = await response.json();
            
            // Display result
            resultCard.classList.remove('hidden');
            
            const isSpam = result.is_spam;
            const spamProbability = result.spam_probability;
            
            // Update UI
            if (isSpam) {
                resultHeader.classList.add('spam');
                resultTitle.textContent = 'Spam Detected';
            } else {
                resultHeader.classList.remove('spam');
                resultTitle.textContent = 'Not Spam';
            }
            
            // Update probability bar
            const percentage = Math.round(spamProbability * 100);
            probabilityBar.style.width = `${percentage}%`;
            probabilityValue.textContent = `${percentage}%`;
            
            // Update bar color based on probability
            if (percentage > 75) {
                probabilityBar.style.backgroundColor = '#f44336'; // Red
            } else if (percentage > 40) {
                probabilityBar.style.backgroundColor = '#ff9800'; // Orange
            } else {
                probabilityBar.style.backgroundColor = '#4CAF50'; // Green
            }
            
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred while checking the message.');
        } finally {
            // Reset button state
            checkButton.disabled = false;
            checkButton.textContent = 'Check for Spam';
        }
    });
});