# Generated by Django 3.1.5 on 2021-03-04 05:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goods', '0003_auto_20210303_2142'),
    ]

    operations = [
        migrations.AlterField(
            model_name='goodssku',
            name='intro',
            field=models.CharField(default='', max_length=256, verbose_name='商品简介'),
        ),
    ]