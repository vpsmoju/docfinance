document.addEventListener('DOMContentLoaded', function() {
    // Configurar a data atual
    const configurarDataAtual = () => {
        const dataAtualElement = document.getElementById('dataAtual');
        if (dataAtualElement) {
            const hoje = new Date();
            const dia = hoje.getDate();
            const meses = [
                'janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
                'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro'
            ];
            const mes = meses[hoje.getMonth()];
            const ano = hoje.getFullYear();
            dataAtualElement.textContent = `Moju(PA), ${dia} de ${mes} de ${ano}.`;
        }
    };

    // Configurar o número do ofício
    const configurarNumeroOficio = () => {
        const numeroOficioInput = document.getElementById('numeroOficio');
        const numeroOficioTexto = document.getElementById('numeroOficioTexto');
        const anoOficioElement = document.getElementById('anoOficio');
        
        if (anoOficioElement) {
            anoOficioElement.textContent = new Date().getFullYear();
        }
        
        if (numeroOficioInput && numeroOficioTexto) {
            numeroOficioInput.addEventListener('input', function() {
                numeroOficioTexto.textContent = this.value || '_____';
            });
        }
    };

    // Inicializar todas as funcionalidades
    configurarDataAtual();
    configurarNumeroOficio();
    // Removemos qualquer referência à impressão aqui
});