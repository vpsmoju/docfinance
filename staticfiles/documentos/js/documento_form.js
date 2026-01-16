// Função para formatar valores monetários no padrão brasileiro
function formatarMoeda(valor) {
    if (valor === null || valor === undefined || valor === '') return '0,00';
    
    // Converte para número e fixa 2 casas decimais
    const numero = parseFloat(valor).toFixed(2);
    
    // Substitui ponto por vírgula e adiciona separador de milhar
    return numero.toString()
        .replace('.', ',')
        .replace(/\B(?=(\d{3})+(?!\d))/g, '.');
}

// Função para converter valor formatado para número
function converterParaNumero(valorFormatado) {
    if (!valorFormatado) return 0;
    
    // Remove pontos e substitui vírgula por ponto
    return parseFloat(valorFormatado.replace(/\./g, '').replace(',', '.'));
}

// Função para calcular o valor líquido
function calcularValorLiquido() {
    // Obter valores dos campos
    const valorBruto = converterParaNumero(document.getElementById('valor_bruto').value) || 0;
    const valorIss = converterParaNumero(document.getElementById('valor_iss').value) || 0;
    const valorIrrf = converterParaNumero(document.getElementById('valor_irrf').value) || 0;
    
    // Calcular valor líquido
    const valorLiquido = valorBruto - valorIss - valorIrrf;
    
    // Atualizar o campo de valor líquido formatado
    document.getElementById('valor_liquido').value = formatarMoeda(valorLiquido);
    
    // Atualizar os campos ocultos com valores numéricos para o backend
    document.getElementById('hidden_valor_documento').value = valorBruto.toFixed(2);
    document.getElementById('hidden_valor_iss').value = valorIss.toFixed(2);
    document.getElementById('hidden_valor_irrf').value = valorIrrf.toFixed(2);
    document.getElementById('hidden_valor_liquido').value = valorLiquido.toFixed(2);
}

// Função para formatar o campo quando o usuário sai dele
function formatarCampoMoeda(campo) {
    const valor = converterParaNumero(campo.value);
    campo.value = formatarMoeda(valor);
}

// Função para formatar CPF/CNPJ
function formatarCpfCnpj(valor) {
    // Remove tudo que não é dígito
    valor = valor.replace(/\D/g, '');
    
    if (valor.length <= 11) {
        // CPF
        return valor.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/g, '$1.$2.$3-$4');
    } else {
        // CNPJ
        return valor.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/g, '$1.$2.$3/$4-$5');
    }
}

// Inicializar os valores quando o documento estiver pronto
document.addEventListener('DOMContentLoaded', function() {
    // Obter referências aos campos
    const valorBrutoInput = document.getElementById('valor_bruto');
    const valorIssInput = document.getElementById('valor_iss');
    const valorIrrfInput = document.getElementById('valor_irrf');
    const valorLiquidoInput = document.getElementById('valor_liquido');
    
    // Verificar se estamos em modo de edição
    const isEditing = document.getElementById('is_editing').value === 'true';
    
    if (isEditing) {
        // Preencher os campos visíveis com os valores iniciais formatados
        const valorDocumentoInicial = document.getElementById('valor_documento_inicial').value || 0;
        const valorIssInicial = document.getElementById('valor_iss_inicial').value || 0;
        const valorIrrfInicial = document.getElementById('valor_irrf_inicial').value || 0;
        
        valorBrutoInput.value = formatarMoeda(valorDocumentoInicial);
        valorIssInput.value = formatarMoeda(valorIssInicial);
        valorIrrfInput.value = formatarMoeda(valorIrrfInicial);
        
        // Calcular o valor líquido inicial
        calcularValorLiquido();
    } else {
        // Para novo documento, inicializar com zeros formatados
        valorBrutoInput.value = '0,00';
        valorIssInput.value = '0,00';
        valorIrrfInput.value = '0,00';
        valorLiquidoInput.value = '0,00';
        
        // Definir status padrão como pendente
        document.getElementById('hidden_status').value = 'PEN';
    }
    
    // Adicionar listeners para os campos de valor
    // Ao sair do campo, formatar o valor
    valorBrutoInput.addEventListener('blur', function() {
        formatarCampoMoeda(this);
        calcularValorLiquido();
    });
    
    valorIssInput.addEventListener('blur', function() {
        formatarCampoMoeda(this);
        calcularValorLiquido();
    });
    
    valorIrrfInput.addEventListener('blur', function() {
        formatarCampoMoeda(this);
        calcularValorLiquido();
    });
    
    // Ao focar no campo, limpar o valor zero para facilitar digitação
    valorBrutoInput.addEventListener('focus', function() {
        if (this.value === '0,00') {
            this.value = '';
        } else {
            // Manter o valor, mas sem formatação de milhar para facilitar edição
            this.value = converterParaNumero(this.value).toString().replace('.', ',');
        }
    });
    
    valorIssInput.addEventListener('focus', function() {
        if (this.value === '0,00') {
            this.value = '';
        } else {
            this.value = converterParaNumero(this.value).toString().replace('.', ',');
        }
    });
    
    valorIrrfInput.addEventListener('focus', function() {
        if (this.value === '0,00') {
            this.value = '';
        } else {
            this.value = converterParaNumero(this.value).toString().replace('.', ',');
        }
    });
    
    // Garantir que o formulário atualize os campos ocultos antes de enviar
    const formulario = document.getElementById('documentoForm');
    if (formulario) {
        formulario.addEventListener('submit', function(event) {
            // Atualizar os campos ocultos uma última vez
            calcularValorLiquido();
        });
    }
    
    // Adicionar máscara ao campo CPF/CNPJ
    const cpfCnpjInput = document.getElementById('cnpj_cpf');
    if (cpfCnpjInput) {
        cpfCnpjInput.addEventListener('input', function(e) {
            let valor = e.target.value.replace(/\D/g, '');
            
            // Limitar o tamanho máximo
            if (valor.length > 14) {
                valor = valor.slice(0, 14);
            }
            
            // Aplicar a máscara
            e.target.value = formatarCpfCnpj(valor);
        });
        
        // Ao sair do campo, buscar fornecedor
        cpfCnpjInput.addEventListener('blur', function() {
            const valor = this.value.replace(/\D/g, '');
            if (valor.length >= 11) {
                buscarFornecedor(valor);
            } else if (valor.length > 0) {
                this.value = ''; // Limpar se estiver incompleto
            }
        });
    }

    // =============================
    // Regras de descontos por tipo
    // =============================
    const tipoSelect = document.getElementById('id_tipo');
    const descontosContainer = document.getElementById('descontos_container');
    const grupoIss = document.getElementById('grupo_iss');
    const grupoIrrf = document.getElementById('grupo_irrf');
    const sectionIss = document.getElementById('section_iss');
    const sectionIrrf = document.getElementById('section_irrf');

    const radioNone = document.getElementById('desconto_none');
    const radioIss = document.getElementById('desconto_iss');
    const radioIrrf = document.getElementById('desconto_irrf');
    const radioIssIrrf = document.getElementById('desconto_iss_irrf');

    function show(el) { if (el) el.style.display = ''; }
    function hide(el) { if (el) el.style.display = 'none'; }
    function setZero(input) {
        if (!input) return;
        input.value = '0,00';
    }
    function disable(input) { if (input) input.disabled = true; }
    function enable(input) { if (input) input.disabled = false; }

    function showRadio(id, visible) {
        const input = document.getElementById(id);
        const label = document.querySelector(`label[for="${id}"]`);
        if (!input || !label) return;
        input.style.display = visible ? '' : 'none';
        label.style.display = visible ? '' : 'none';
    }

    function updateDescontoUI() {
        const selected = document.querySelector('input[name="desconto_opcao"]:checked')?.value || 'NONE';

        if (selected === 'NONE') {
            hide(sectionIss);
            hide(sectionIrrf);
            setZero(valorIssInput);
            setZero(valorIrrfInput);
            enable(valorBrutoInput);
            disable(valorIssInput);
            disable(valorIrrfInput);
        } else if (selected === 'ISS') {
            show(sectionIss);
            hide(sectionIrrf);
            enable(valorIssInput);
            disable(valorIrrfInput);
            setZero(valorIrrfInput);
        } else if (selected === 'IRRF') {
            hide(sectionIss);
            show(sectionIrrf);
            disable(valorIssInput);
            enable(valorIrrfInput);
            setZero(valorIssInput);
        } else if (selected === 'ISS_IRRF') {
            show(sectionIss);
            show(sectionIrrf);
            enable(valorIssInput);
            enable(valorIrrfInput);
        }
        calcularValorLiquido();
    }

    function aplicarRegrasPorTipo() {
        const tipo = tipoSelect ? tipoSelect.value : '';
        if (!tipo) return;

        // Mostrar/ocultar opções de desconto conforme o tipo
        if (tipo === 'NF' || tipo === 'FAT') {
            // Sem descontos para Nota Fiscal e Fatura
            hide(descontosContainer);
            radioNone.checked = true;
            updateDescontoUI();
        } else if (tipo === 'NFS' || tipo === 'NFSA') {
            // Quatro casos: nenhum, ISS, IRRF, ISS+IRRF
            show(descontosContainer);
            showRadio('desconto_none', true);
            showRadio('desconto_iss', true);
            showRadio('desconto_irrf', true);
            showRadio('desconto_iss_irrf', true);

            updateDescontoUI();
        } else if (tipo === 'REC') {
            // Quatro casos: nenhum, ISS, IRRF, ISS+IRRF
            show(descontosContainer);
            showRadio('desconto_none', true);
            showRadio('desconto_iss', true);
            showRadio('desconto_irrf', true);
            showRadio('desconto_iss_irrf', true);

            updateDescontoUI();
        }
    }

    // Listeners de desconto
    [radioNone, radioIss, radioIrrf, radioIssIrrf].forEach(r => {
        if (r) {
            r.addEventListener('change', updateDescontoUI);
        }
    });

    if (tipoSelect) {
        tipoSelect.addEventListener('change', aplicarRegrasPorTipo);
        aplicarRegrasPorTipo();
    }

    // Se em edição, tentar marcar a opção de desconto baseada nos valores atuais
    if (isEditing) {
        const issValor = converterParaNumero(valorIssInput.value);
        const irrfValor = converterParaNumero(valorIrrfInput.value);
        if ((issValor > 0) && (irrfValor > 0) && radioIssIrrf) {
            radioIssIrrf.checked = true;
        } else if (issValor > 0 && radioIss) {
            radioIss.checked = true;
        } else if (irrfValor > 0 && radioIrrf) {
            radioIrrf.checked = true;
        } else if (radioNone) {
            radioNone.checked = true;
        }
        updateDescontoUI();
    }

    // Função para buscar fornecedor por CPF/CNPJ
    function buscarFornecedor(cpfCnpj) {
        fetch(`/documentos/api/buscar-fornecedor/?cnpj_cpf=${cpfCnpj}`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    console.log('Fornecedor não encontrado');
                    // Limpar o campo de fornecedor
                    const fornecedorSelect = document.getElementById('id_fornecedor');
                    fornecedorSelect.value = '';
                } else {
                    // Preencher o campo de fornecedor com o ID retornado
                    const fornecedorSelect = document.getElementById('id_fornecedor');
                    fornecedorSelect.value = data.id;
                }
            })
            .catch(error => {
                console.error('Erro ao buscar fornecedor:', error);
            });
    }
});
