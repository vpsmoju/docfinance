# DocFinance

Guia rápido para desenvolvimento e padrões de estilos.

## Estilos (CSS)
- Evite estilos inline nos templates (alerta: "Inline styles should be avoided. (H021)").
- Prefira utilitários do Bootstrap e classes utilitárias próprias em `static/css/custom.css`.
- Utilitários disponíveis:
  - `h-70vh`, `max-w-50vw`, `max-w-680`, `max-h-60vh`, `z-1050`, `z-1055`, `py-375`.
- Exemplos de migração:
  - `style="width:100%; height:70vh; border:0"` → `class="w-100 h-70vh border-0"`.
  - `style="max-width:50vw"` → `class="max-w-50vw"`.
  - `style="z-index:1050"` → `class="z-1050"`.
- Se precisar de novos utilitários, adicione-os em `static/css/custom.css` e reutilize nos templates.

## Cache-busting de JavaScript
- Para evitar servir versões antigas após alterações, adicione um sufixo de versão nas tags `<script>`:
  - `{% static 'documentos/js/documento_data.js' %}?v=2`
- Atualize o número da versão quando modificar o arquivo para forçar o navegador a baixar o novo conteúdo.

## Arquivos estáticos
- Desenvolvimento:
  - `STATIC_URL = 'static/'`
  - `STATICFILES_DIRS = [BASE_DIR / 'static']`
  - `STATIC_ROOT = BASE_DIR / 'staticfiles'` (destino de `collectstatic`).
- Produção:
  - Não edite `staticfiles/` manualmente; ele é gerado por `collectstatic`.
  - Após alterar CSS/JS, execute `python manage.py collectstatic` para atualizar `staticfiles/`.
- Dica: faça hard refresh no navegador (`Ctrl+F5`) após mudanças de CSS/JS.

## Lint e qualidade
- Se o linter sinalizar `H021 Inline styles should be avoided`, mova estilos para classes utilitárias conforme acima.
