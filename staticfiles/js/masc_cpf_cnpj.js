/**
 * Dependências necessárias:
 * - jQuery
 * - jQuery Mask Plugin
 */
document.addEventListener('DOMContentLoaded', function() {
    const cnpjCpfField = document.getElementById('id_cnpj_cpf');
    const tipoField = document.getElementById('id_tipo');
    const telefoneField = document.getElementById('id_telefone');
    const formValidation = document.querySelector('.needs-validation');

    if (cnpjCpfField && tipoField) {
        // Função para aplicar a máscara correta
        function aplicarMascara() {
            const tipo = tipoField.value;
            const value = $(cnpjCpfField).val().replace(/\D/g, '');
            
            if (tipo === 'PF') {
                $(cnpjCpfField).mask('000.000.000-00');
                // Limita o campo a 11 dígitos para CPF
                if (value.length > 11) {
                    $(cnpjCpfField).val(value.substr(0, 11));
                }
            } else {
                $(cnpjCpfField).mask('00.000.000/0000-00');
                // Limita o campo a 14 dígitos para CNPJ
                if (value.length > 14) {
                    $(cnpjCpfField).val(value.substr(0, 14));
                }
            }
        }

        // Aplica máscara quando o tipo é alterado
        $(tipoField).on('change', aplicarMascara);

        // Aplica máscara quando o campo é modificado
        $(cnpjCpfField).on('input', aplicarMascara);

        // Aplica máscara inicial
        aplicarMascara();
    }

    // Máscara para telefone
    if (telefoneField) {
        $(telefoneField).mask('(00) 00000-0000');
    }
    
    // Sanitização e validação do formulário
    if (formValidation) {
        $(formValidation).on('submit', function(event) {
            // Remover máscara e enviar apenas dígitos para CNPJ/CPF
            if (cnpjCpfField && tipoField) {
                const tipo = tipoField.value;
                const apenasDigitos = ($(cnpjCpfField).val() || '').replace(/\D/g, '');
                if (tipo === 'PF') {
                    $(cnpjCpfField).val(apenasDigitos.slice(0, 11));
                } else {
                    $(cnpjCpfField).val(apenasDigitos.slice(0, 14));
                }
            }

            if (!this.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            $(this).addClass('was-validated');
        });
    }
});
