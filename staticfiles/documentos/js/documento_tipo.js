document.addEventListener('DOMContentLoaded', function() {
    // Controle do campo número do documento baseado no tipo
    const tipoSelect = document.getElementById('id_tipo');
    const numeroDocumentoDiv = document.getElementById('div_numero_documento');
    const numeroDocumentoInput = document.getElementById('id_numero_documento');
    const numeroInput = document.querySelector('input[name="numero"]');
    
    function handleTipoChange() {
        if (tipoSelect.value === 'REC') { // Assumindo que 'REC' é o valor para Recibo
            numeroDocumentoDiv.style.display = 'none';
            // Se for um recibo, o número do documento deve ser igual ao número
            if (numeroInput && numeroInput.value) {
                numeroDocumentoInput.value = numeroInput.value;
            }
        } else {
            numeroDocumentoDiv.style.display = 'block';
        }
    }
    
    // Executar na inicialização
    if (tipoSelect) {
        handleTipoChange();
        
        // Adicionar listener para mudanças no tipo
        tipoSelect.addEventListener('change', handleTipoChange);
    }
});