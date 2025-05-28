function showToastNotification(message, duration = 3000) {
    // Remover notificações existentes
    const existingToasts = document.querySelectorAll('.toast-notification');
    existingToasts.forEach(toast => toast.remove());
    
    // Criar nova notificação
    const toast = document.createElement('div');
    toast.className = 'toast-notification';
    
    // Substituir \n por <br> para quebras de linha HTML
    message = message.replace(/\n/g, '<br>');
    toast.innerHTML = message;
    
    // Adicionar ao DOM
    document.body.appendChild(toast);
    
    // Remover após o tempo especificado
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, duration);
}