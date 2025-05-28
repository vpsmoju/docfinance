document.addEventListener('DOMContentLoaded', function() {
    const cnpjCpfInput = document.getElementById('cnpj_cpf');
    const fornecedorDisplay = document.getElementById('fornecedor_display');
    const fornecedorHidden = document.getElementById('id_fornecedor');
    
    if (cnpjCpfInput && fornecedorDisplay && fornecedorHidden) {
        cnpjCpfInput.addEventListener('blur', function() {
            if (this.value) {
                // Usar a API existente para buscar o fornecedor
                fetch(`/documentos/api/buscar-fornecedor/?cnpj_cpf=${this.value}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.error) {
                            fornecedorDisplay.value = 'Fornecedor não encontrado';
                            fornecedorHidden.value = '';
                        } else {
                            fornecedorDisplay.value = data.nome;
                            fornecedorHidden.value = data.id;
                        }
                    })
                    .catch(error => {
                        console.error('Erro ao buscar fornecedor:', error);
                        fornecedorDisplay.value = 'Erro ao buscar fornecedor';
                    });
            } else {
                fornecedorDisplay.value = 'Será preenchido pelo CPF/CNPJ';
                fornecedorHidden.value = '';
            }
        });
    }
});
