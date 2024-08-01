document.getElementById('prompt').addEventListener('keypress', async function(event) {
    if (event.key === 'Enter') {
        const url = this.value.trim();
        const youtubeRegex = /^(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:watch\?v=|embed\/|v\/)|youtu\.be\/)([\w-]{11})/;
        const match = url.match(youtubeRegex);
    
        if (match) {
            const videoId = match[1];
            const embedUrl = `https://www.youtube.com/embed/${videoId}`;
            document.getElementById('videoPlaceholder').innerHTML = `
                <iframe width="100%" height="390" src="${embedUrl}" frameborder="0" allowfullscreen></iframe>
            `;
            
            try {
                const response = await fetch('/process', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        action: 'transcribe',
                        input: url,
                    }),
                });
                
                const data = await response.json();
                
                if (data.status === 'success') {
                    const chatBox = document.getElementById('chatBox');
                    const summaryElement = document.createElement('div');
                    summaryElement.className = 'chat-message ai';
                    summaryElement.textContent = data.summary;
                    chatBox.innerHTML = '';
                    chatBox.appendChild(summaryElement);
                } else {
                    alert(data.message);
                }
            } catch (error) {
                console.error('Error:', error);
                alert('An error occurred while processing the request.');
            }
        } else {
            alert('Invalid YouTube URL');
        }
    }
});

document.getElementById('chatSubmitButton').addEventListener('click', async function() {
    const chatBox = document.getElementById('chatBox-1');
    const chatInput = document.getElementById('chatInput');
    const userMessage = chatInput.value.trim();
    
    if (userMessage) {
        const messageElement = document.createElement('div');
        messageElement.className = 'chat-message user';
        messageElement.textContent = userMessage;
        chatBox.innerHTML = '';
        chatBox.appendChild(messageElement);
    
        try {
            const response = await fetch('/process', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    action: 'ask',
                    input: userMessage,
                }),
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                const aiResponseElement = document.createElement('div');
                aiResponseElement.className = 'chat-message ai';
                aiResponseElement.textContent = data.answer;
                chatBox.appendChild(aiResponseElement);
            } else {
                const errorElement = document.createElement('div');
                errorElement.className = 'chat-message ai';
                errorElement.textContent = data.message;
                chatBox.appendChild(errorElement);
            }
        } catch (error) {
            console.error('Error:', error);
            const errorElement = document.createElement('div');
            errorElement.className = 'chat-message ai';
            errorElement.textContent = 'An error occurred while processing your request.';
            chatBox.appendChild(errorElement);
        }
    
        chatInput.value = '';
        chatBox.scrollTop = chatBox.scrollHeight;
    }
});