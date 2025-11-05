document.addEventListener('DOMContentLoaded', function() {
    const cnpjCpfInput = document.getElementById('cnpj_cpf');
    const fornecedorDisplay = document.getElementById('fornecedor_display');
    const fornecedorHidden = document.getElementById('id_fornecedor');
    const modalEl = document.getElementById('fornecedorNaoEncontradoModal');
    const cadastrarBtn = document.getElementById('btnCadastrarFornecedor');
    const cadastroModalEl = document.getElementById('cadastroFornecedorModal');
    const cadastroIframe = document.getElementById('iframeCadastroFornecedor');
    let fornecedorModalInstance = null;
    let cadastroModalInstance = null;
    
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
                            if (modalEl) {
                                if (!fornecedorModalInstance && window.bootstrap) {
                                    fornecedorModalInstance = new bootstrap.Modal(modalEl);
                                }
                                fornecedorModalInstance && fornecedorModalInstance.show();
                            }
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

    // Botão do modal para abrir o cadastro de fornecedor
    if (cadastrarBtn) {
        cadastrarBtn.addEventListener('click', function() {
            const docUrl = window.location.pathname; // ex.: /documentos/novo/
            const cnpjAtual = cnpjCpfInput ? encodeURIComponent(cnpjCpfInput.value) : '';
            const url = `/fornecedores/novo/?cnpj_cpf=${cnpjAtual}&embed=true`;
            // Fechar modal de aviso, se aberto
            if (!fornecedorModalInstance && window.bootstrap && modalEl) {
                fornecedorModalInstance = new bootstrap.Modal(modalEl);
            }
            fornecedorModalInstance && fornecedorModalInstance.hide();

            // Abrir modal de cadastro com iframe
            if (!cadastroModalInstance && window.bootstrap && cadastroModalEl) {
                cadastroModalInstance = new bootstrap.Modal(cadastroModalEl);
            }
            if (cadastroIframe) {
                cadastroIframe.src = url;
            }
            cadastroModalInstance && cadastroModalInstance.show();
        });
    }

    // Ouvir retorno do iframe quando fornecedor for criado/atualizado
    window.addEventListener('message', function(event) {
        const data = event.data || {};
        const tipoMsg = data.type;
        if ((tipoMsg === 'fornecedor_created' || tipoMsg === 'fornecedor_updated') && data.id) {
            // Preencher campos no formulário de documento
            if (fornecedorDisplay) fornecedorDisplay.value = data.nome || 'Fornecedor selecionado';
            if (fornecedorHidden) fornecedorHidden.value = data.id;
            // Fechar modal de cadastro
            cadastroModalInstance && cadastroModalInstance.hide();
            // Notificação amigável
            if (typeof showToastNotification === 'function') {
                const msg = tipoMsg === 'fornecedor_updated' ? 'Fornecedor atualizado e vinculado' : 'Fornecedor cadastrado e vinculado';
                showToastNotification(msg);
            }
        }
    });
});
