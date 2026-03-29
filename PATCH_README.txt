FIX PATCH: stage29 base.html

Проблема:
- в base.html был дублирован блок `{% block content %}`
- из-за этого Jinja падал с:
  TemplateAssertionError: block 'content' defined twice

Что заменить:
- app/web/templates/base.html

После замены:
- redeploy
- снова открыть /admin/card-builder
