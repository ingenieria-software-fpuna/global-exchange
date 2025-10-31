# Generated manually on 2025-01-XX

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transacciones', '0007_merge_20251024_0734'),
    ]

    operations = [
        migrations.AlterField(
            model_name='estadotransaccion',
            name='codigo',
            field=models.CharField(
                choices=[
                    ('PENDIENTE', 'Pendiente de Pago'),
                    ('PAGADA', 'Pagada'),
                    ('ENTREGADA', 'Entregada'),
                    ('RETIRADO', 'Retirado'),
                    ('CANCELADA', 'Cancelada'),
                    ('ANULADA', 'Anulada'),
                ],
                max_length=15,
                unique=True,
                verbose_name='Código del estado'
            ),
        ),
    ]

