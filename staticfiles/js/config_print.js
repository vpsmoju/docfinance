document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM carregado, procurando botão de impressão...");
    
    // Variável para controlar se a impressão já foi iniciada
    let impressaoIniciada = false;
    let impressaoTimer = null;
    
    // Remover qualquer listener existente para beforeprint e afterprint
    const noop = function() {};
    window.removeEventListener('beforeprint', noop);
    window.removeEventListener('afterprint', noop);
    
    // Função para lidar com o evento afterprint
    const handleAfterPrint = function() {
        console.log("Impressão finalizada ou cancelada");
        document.body.classList.remove('printing');
        impressaoIniciada = false;
        
        // Limpar qualquer timer pendente
        if (impressaoTimer) {
            clearTimeout(impressaoTimer);
            impressaoTimer = null;
        }
    };
    
    // Adicionar novo listener para afterprint
    window.addEventListener('afterprint', handleAfterPrint);
    
    // Adicionar funcionalidade de impressão específica para este relatório
    const printButton = document.getElementById('printReport');
    console.log("Botão de impressão encontrado:", printButton);
    
    if (printButton) {
        // Remover qualquer listener existente (se possível)
        const novoButton = printButton.cloneNode(true);
        printButton.parentNode.replaceChild(novoButton, printButton);
        
        // Adicionar novo listener
        novoButton.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            console.log("Botão de impressão clicado!");
            
            // Evitar múltiplos cliques
            if (impressaoIniciada) {
                console.log("Impressão já iniciada, ignorando clique adicional");
                return false;
            }
            
            // Marcar que a impressão foi iniciada
            impressaoIniciada = true;
            
            // Preparar para impressão
            document.body.classList.add('printing');
            
            // Definir um timer para resetar o estado caso a impressão não seja concluída
            impressaoTimer = setTimeout(function() {
                console.log("Resetando estado de impressão após timeout");
                document.body.classList.remove('printing');
                impressaoIniciada = false;
                impressaoTimer = null;
            }, 5000);
            
            // Abrir diálogo de impressão com um pequeno atraso
            setTimeout(function() {
                window.print();
            }, 200);
        });
    } else {
        console.error("Botão de impressão não encontrado!");
    }
});