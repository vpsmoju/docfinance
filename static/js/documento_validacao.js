document.addEventListener('DOMContentLoaded', function() {
    // Verificar se há mensagens de erro do Django
    const djangoErrors = document.querySelectorAll('.errorlist');
    if (djangoErrors.length > 0) {
        const errorList = document.getElementById('error-list');
        errorList.innerHTML = '';
        
        djangoErrors.forEach(function(errorElement) {
            const errorItems = errorElement.querySelectorAll('li');
            errorItems.forEach(function(item) {
                const li = document.createElement('li');
                li.textContent = item.textContent;
                errorList.appendChild(li);
            });
        });
        
        document.getElementById('form-errors').classList.remove('d-none');
    }
});