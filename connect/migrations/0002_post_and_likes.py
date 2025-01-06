from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings

class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('connect', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderitem',
            name='assigned_rider',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='delivery_items',
                to='connect.bodarider'
            ),
        ),
        migrations.AddField(
            model_name='orderitem',
            name='delivery_fee',
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                max_digits=10
            ),
        ),
    ] 