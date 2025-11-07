document.addEventListener('DOMContentLoaded', function () {
  const dataDocumentoInput = document.getElementById('id_data_documento');
  if (!dataDocumentoInput) return;

  // Se o input for do tipo "date", ele exige ISO (YYYY-MM-DD).
  // Não devemos reescrever para dd/mm/aaaa, pois isso apaga o valor.
  if (dataDocumentoInput.type === 'date') {
    const v = dataDocumentoInput.value;
    // Caso tenha vindo em dd/mm/aaaa por algum motivo, normaliza para ISO.
    const m = v && v.match(/^([0-3]?\d)\/([0-1]?\d)\/(\d{4})$/);
    if (m) {
      const [_, d, mth, y] = m;
      dataDocumentoInput.value = `${y}-${mth.padStart(2, '0')}-${d.padStart(2, '0')}`;
    }
    return;
  }

  // Para inputs texto (se algum template alternativo usar), podemos exibir em dd/mm/aaaa.
  const v = dataDocumentoInput.value;
  const iso = v && v.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (iso) {
    const [_, y, mth, d] = iso;
    dataDocumentoInput.value = `${d}/${mth}/${y}`;
  }
});
