from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("documentos", "0005_documento_etapa_historicodocumento"),
    ]

    operations = [
        migrations.AddField(
            model_name="documento",
            name="processo",
            field=models.CharField(
                max_length=50, blank=True, null=True, verbose_name="Processo"
            ),
        ),
    ]

