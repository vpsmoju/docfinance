document.addEventListener('DOMContentLoaded', function() {
    // Formatar a data para o formato brasileiro
    const dataDocumentoInput = document.getElementById('id_data_documento');
    if (dataDocumentoInput) {
        // Converter formato yyyy-mm-dd para dd/mm/yyyy
        dataDocumentoInput.addEventListener('change', function() {
            const dataOriginal = this.value;
            if (dataOriginal) {
                const partes = dataOriginal.split('-');
                if (partes.length === 3) {
                    // Formatar como dd/mm/yyyy
                    const dataFormatada = `${partes[2]}/${partes[1]}/${partes[0]}`;
                    console.log('Data formatada:', dataFormatada);
                    // Se necessário, atualizar um campo oculto com a data formatada
                    const hiddenDataInput = document.getElementById('hidden_data_documento');
                    if (hiddenDataInput) {
                        hiddenDataInput.value = dataFormatada;
                    }
                }
            }
        });
        
        // Se estiver em modo de edição, formatar a data inicial
        const isEditing = document.getElementById('is_editing');
        if (isEditing && isEditing.value === 'true') {
            const dataOriginal = dataDocumentoInput.value;
            if (dataOriginal && dataOriginal.includes('-')) {
                const partes = dataOriginal.split('-');
                if (partes.length === 3) {
                    // Formatar como dd/mm/yyyy para exibição
                    dataDocumentoInput.value = `${partes[2]}/${partes[1]}/${partes[0]}`;
                }
            }
        }
    }
});