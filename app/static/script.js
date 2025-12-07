// Handle color presets
document.querySelectorAll('.color-preset').forEach(btn => {
    btn.addEventListener('click', () => {
        const color = btn.getAttribute('data-color');
        document.getElementById('subtitle-color').value = color;
    });
});

// Handle emoji buttons
document.querySelectorAll('.emoji-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const emoji = btn.getAttribute('data-emoji');
        const emojiInput = document.getElementById('emojis');
        emojiInput.value = emoji;
    });
});

// Enable/disable effect selects based on checkboxes
document.getElementById('speed-effect').addEventListener('change', (e) => {
    document.getElementById('speed-value').disabled = !e.target.checked;
});

document.getElementById('fadein-effect').addEventListener('change', (e) => {
    document.getElementById('fadein-value').disabled = !e.target.checked;
});

document.getElementById('fadeout-effect').addEventListener('change', (e) => {
    document.getElementById('fadeout-value').disabled = !e.target.checked;
});

// Form submission
document.getElementById('clip-form').addEventListener('submit', async (event) => {
    event.preventDefault();

    const youtubeUrl = document.getElementById('youtube-url').value;
    const subtitleColor = document.getElementById('subtitle-color').value;
    const emojis = document.getElementById('emojis').value;
    const scheduleInterval = document.getElementById('schedule-interval').value;
    const scheduleUnit = document.getElementById('schedule-unit').value;

    // Build effects string from checkboxes
    const effects = [];
    if (document.getElementById('speed-effect').checked) {
        const speed = document.getElementById('speed-value').value;
        effects.push(`speed:${speed}`);
    }
    if (document.getElementById('fadein-effect').checked) {
        const fadein = document.getElementById('fadein-value').value;
        effects.push(`fadein:${fadein}`);
    }
    if (document.getElementById('fadeout-effect').checked) {
        const fadeout = document.getElementById('fadeout-value').value;
        effects.push(`fadeout:${fadeout}`);
    }
    const effectsString = effects.join(',');

    const responseContainer = document.getElementById('response');
    const progressContainer = document.getElementById('progress');

    // Show progress, hide previous results
    responseContainer.innerHTML = '';
    responseContainer.style.display = 'none';
    progressContainer.style.display = 'block';

    try {
        const response = await fetch('/api/clip', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                url: youtubeUrl,
                subtitle_color: subtitleColor,
                emojis: emojis || null,
                effects: effectsString || null,
                schedule_interval: scheduleInterval || null,
                schedule_unit: (scheduleUnit && scheduleInterval) ? scheduleUnit : null
            })
        });

        const data = await response.json();

        // Hide progress
        progressContainer.style.display = 'none';
        responseContainer.style.display = 'block';

        if (response.ok) {
            const clipsList = data.paths && data.paths.length > 0
                ? data.paths.map((path, i) => `<li>Clip ${i + 1}: ${path}</li>`).join('')
                : '<li>No clips generated</li>';

            responseContainer.innerHTML = `
                <div class="success-message">
                    <h2>✅ ${data.message}</h2>
                    <div class="result-section">
                        <h3>📁 Generated Clips (${data.clips_generated || 0}):</h3>
                        <ul>${clipsList}</ul>
                    </div>
                    <div class="result-section">
                        <h3>📝 Transcription Method:</h3>
                        <p><strong>${data.transcription_method === 'youtube_captions' ? '⚡ YouTube Captions (Instant!)' : '🎤 Whisper Transcription'}</strong></p>
                    </div>
                    <div class="result-section">
                        <h3>📄 Full Transcription:</h3>
                        <p class="transcription-text">${data.transcription ? data.transcription.substring(0, 500) + '...' : 'No transcription available'}</p>
                    </div>
                </div>
            `;
        } else {
            responseContainer.innerHTML = `
                <div class="error-message">
                    <h2>❌ Error</h2>
                    <p>${data.error}</p>
                </div>
            `;
        }
    } catch (error) {
        progressContainer.style.display = 'none';
        responseContainer.style.display = 'block';
        responseContainer.innerHTML = `
            <div class="error-message">
                <h2>❌ Error</h2>
                <p>${error.message}</p>
            </div>
        `;
    }
});
