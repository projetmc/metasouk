# Generated by Django 5.0.2 on 2025-05-10 10:18

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('metasouk', '0009_remove_articlecommande_commande_id_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='commande',
            name='utilisateur_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='commandes', to='metasouk.utilisateur'),
        ),
    ]
