document.addEventListener('DOMContentLoaded', function() {
    const secretariaSelect = document.getElementById('id_secretaria');
    const recursoSelect = document.getElementById('id_recurso');
    const recursoInicial = recursoSelect ? recursoSelect.getAttribute('data-initial-recurso') : null;

    if (!secretariaSelect || !recursoSelect) {
        console.error('Elementos do formulário não encontrados');
        return;
    }

    async function carregarRecursos(secretariaId) {
        recursoSelect.innerHTML = '';
        const opcaoVazia = document.createElement('option');
        opcaoVazia.value = '';
        opcaoVazia.textContent = '---------';
        recursoSelect.appendChild(opcaoVazia);

        if (!secretariaId) {
            return;
        }

        try {
            const resp = await fetch(`/documentos/api/recursos-por-secretaria/${secretariaId}/`);
            const data = await resp.json();
            const lista = (data.recursos || []);
            lista.forEach(rec => {
                const opt = document.createElement('option');
                opt.value = rec.id;
                opt.textContent = rec.nome;
                recursoSelect.appendChild(opt);
            });
            if (lista.length === 0) {
                // Indicar claramente que não há recursos para a secretaria selecionada
                const info = document.createElement('option');
                info.value = '';
                info.textContent = 'Nenhum recurso para esta secretaria';
                info.disabled = true;
                recursoSelect.appendChild(info);
            }
            if (recursoInicial) {
                recursoSelect.value = recursoInicial;
            } else if (lista.length === 1) {
                // Se houver apenas um recurso, selecionar automaticamente
                recursoSelect.value = String(lista[0].id);
            }
        } catch (err) {
            console.error('Erro ao carregar recursos:', err);
        }
    }

    secretariaSelect.addEventListener('change', function(e) {
        carregarRecursos(e.target.value);
    });

    // Inicializar com a secretaria atual (se houver)
    carregarRecursos(secretariaSelect.value);
});