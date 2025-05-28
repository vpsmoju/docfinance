document.addEventListener('DOMContentLoaded', function() {
    // Botão para exportar para PDF
    const btnExportarPDF = document.getElementById('btn-exportar-pdf');
    if (btnExportarPDF) {
        btnExportarPDF.addEventListener('click', function() {
            // Preparar os dados do formulário de filtro
            const formData = new FormData(document.getElementById('filtroForm'));
            formData.append('formato', 'pdf');
            
            // Construir a URL com os parâmetros
            const params = new URLSearchParams(formData);
            const currentUrl = window.location.pathname;
            
            // Redirecionar para a URL de exportação
            window.location.href = `${currentUrl}?${params.toString()}`;
        });
    }
    
    // Botão para exportar para Excel
    const btnExportarExcel = document.getElementById('btn-exportar-excel');
    if (btnExportarExcel) {
        btnExportarExcel.addEventListener('click', function() {
            // Preparar os dados do formulário de filtro
            const formData = new FormData(document.getElementById('filtroForm'));
            formData.append('formato', 'excel');
            
            // Construir a URL com os parâmetros
            const params = new URLSearchParams(formData);
            const currentUrl = window.location.pathname;
            
            // Redirecionar para a URL de exportação
            window.location.href = `${currentUrl}?${params.toString()}`;
        });
    }
    
    // Atualizar campos dependentes nos filtros
    const tipoAgrupamento = document.getElementById('tipo_agrupamento');
    if (tipoAgrupamento) {
        tipoAgrupamento.addEventListener('change', function() {
            document.getElementById('filtroForm').submit();
        });
    }
    
    const tipoPeriodo = document.getElementById('tipo_periodo');
    if (tipoPeriodo) {
        tipoPeriodo.addEventListener('change', function() {
            document.getElementById('filtroForm').submit();
        });
    }
});

// Funções para formatação de valores monetários
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

// Configuração padrão para gráficos
function configurarGraficoTorta(ctx, labels, valores, titulo) {
    const backgroundColors = [
        'rgba(54, 162, 235, 0.6)',
        'rgba(255, 99, 132, 0.6)',
        'rgba(255, 206, 86, 0.6)',
        'rgba(75, 192, 192, 0.6)',
        'rgba(153, 102, 255, 0.6)',
        'rgba(255, 159, 64, 0.6)',
        'rgba(199, 199, 199, 0.6)'
    ];
    
    return new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                label: titulo,
                data: valores,
                backgroundColor: backgroundColors,
                borderColor: backgroundColors.map(color => color.replace('0.6', '1')),
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'right',
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.label || '';
                            if (label) {
                                label += ': ';
                            }
                            const value = context.raw;
                            label += new Intl.NumberFormat('pt-BR', { 
                                style: 'currency', 
                                currency: 'BRL' 
                            }).format(value);
                            return label;
                        }
                    }
                }
            }
        }
    });
}

// Configuração para gráficos de barra
function configurarGraficoBarra(ctx, labels, valores, titulo) {
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: titulo,
                data: valores,
                backgroundColor: 'rgba(54, 162, 235, 0.6)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return new Intl.NumberFormat('pt-BR', { 
                                style: 'currency', 
                                currency: 'BRL' 
                            }).format(value);
                        }
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            const value = context.raw;
                            label += new Intl.NumberFormat('pt-BR', { 
                                style: 'currency', 
                                currency: 'BRL' 
                            }).format(value);
                            return label;
                        }
                    }
                }
            }
        }
    });
}