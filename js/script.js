function toggleOption() {
    const message = document.getElementById('message');
    const currentOption = message.innerText === 'Ask' ? 'Url' : 'Ask';
    message.innerText = currentOption;
    message.style.opacity = '1';
    setTimeout(() => {
        message.style.opacity = '0';
    }, 3000);
}