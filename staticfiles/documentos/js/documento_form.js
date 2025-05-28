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