document.addEventListener('DOMContentLoaded', function() {
    // Mapeamento de secretarias para seus recursos
    const recursosPorSecretaria = {
        'EDU': ['FUNDEB', 'DMDE', 'QSE', 'PNAE', 'PETE', 'PEAE', 'PNAT', 'SEDUC_CRECHE', 'MOJU_EDUCA', 'BRALF', 'PDDE', 'CONVENIO_EDU'],
        'ADM': ['GABINETE', 'PREFEITURA', 'SEMAD', 'SEOB', 'SECTEMA', 'ILUM_PUBLICA', 'SEMUSP', 'SEMAGRI', 'LEI_ALDIR_BLANC', 'SECULT', 'SEMAPI', 'SETRANS', 'SEMDESTRE', 'SEFAZ', 'SECDELT', 'CONVENIO_ADM'],
        'ASS': ['FMAS', 'IGD_IGPAB', 'PSB', 'MAC', 'GSUAS', 'PROT_ESPECIAL', 'PROT_BASICA', 'BL_IGD', 'PROCAD_SUAS', 'CRIAN_FELIZ', 'AUX_BRASIL', 'CONVENIO_ASS'],
        'SAU': ['PISO_ENFER', 'CONTRAPARTIDA', 'FUS', 'OUTROS', 'CONVENIO_SAU']
    };
    
    // Elementos do formulário
    const secretariaSelect = document.getElementById('id_secretaria');
    const recursoSelect = document.getElementById('id_recurso');
    
    if (!secretariaSelect || !recursoSelect) {
        console.error('Elementos do formulário não encontrados');
        return;
    }
    
    // Salvar todas as opções originais
    const todasOpcoes = Array.from(recursoSelect.options);
    const opcoesOriginais = [];
    
    todasOpcoes.forEach(opcao => {
        opcoesOriginais.push({
            valor: opcao.value,
            texto: opcao.textContent
        });
    });
    
    // Função para atualizar as opções de recurso
    function atualizarRecursos() {
        const secretariaSelecionada = secretariaSelect.value;
        
        // Se nenhuma secretaria foi selecionada, mostrar todas as opções
        if (!secretariaSelecionada) {
            // Restaurar todas as opções originais
            recursoSelect.innerHTML = '';
            opcoesOriginais.forEach(opcao => {
                const novaOpcao = document.createElement('option');
                novaOpcao.value = opcao.valor;
                novaOpcao.textContent = opcao.texto;
                recursoSelect.appendChild(novaOpcao);
            });
            return;
        }
        
        // Obter recursos para a secretaria selecionada
        const recursosDisponiveis = recursosPorSecretaria[secretariaSelecionada] || [];
        
        // Salvar o valor atual (se possível)
        const valorAtual = recursoSelect.value;
        
        // Limpar opções atuais
        recursoSelect.innerHTML = '';
        
        // Adicionar opção vazia
        const opcaoVazia = document.createElement('option');
        opcaoVazia.value = '';
        opcaoVazia.textContent = '---------';
        recursoSelect.appendChild(opcaoVazia);
        
        // Adicionar apenas os recursos da secretaria selecionada
        opcoesOriginais.forEach(opcao => {
            if (opcao.valor && recursosDisponiveis.includes(opcao.valor)) {
                const novaOpcao = document.createElement('option');
                novaOpcao.value = opcao.valor;
                novaOpcao.textContent = opcao.texto;
                recursoSelect.appendChild(novaOpcao);
            }
        });
        
        // Restaurar valor se ainda for válido
        if (valorAtual && recursosDisponiveis.includes(valorAtual)) {
            recursoSelect.value = valorAtual;
        }
    }
    
    // Atualizar recursos quando a secretaria mudar
    secretariaSelect.addEventListener('change', atualizarRecursos);
    
    // Inicializar com os valores atuais
    atualizarRecursos();
});