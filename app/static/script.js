document.getElementById('clip-form').addEventListener('submit', async (event) => {
    event.preventDefault();

    const form = event.target;
    const formData = new FormData(form);
    const youtubeUrl = formData.get('youtube-url');
    const subtitleColor = formData.get('subtitle-color');
    const emojis = formData.get('emojis');
    const effects = formData.get('effects');
    const responseContainer = document.getElementById('response');

    responseContainer.innerHTML = 'Generating clip...';

    try {
        const response = await fetch('/api/clip', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                url: youtubeUrl,
                subtitle_color: subtitleColor,
                emojis: emojis,
                effects: effects
            })
        });

        const data = await response.json();

        if (response.ok) {
            responseContainer.innerHTML = `
                <p>${data.message}</p>
                <p>Clip path: ${data.path}</p>
                <p>Transcription: ${data.transcription}</p>
            `;
        } else {
            responseContainer.innerHTML = `<p>Error: ${data.error}</p>`;
        }
    } catch (error) {
        responseContainer.innerHTML = `<p>Error: ${error.message}</p>`;
    }
});
