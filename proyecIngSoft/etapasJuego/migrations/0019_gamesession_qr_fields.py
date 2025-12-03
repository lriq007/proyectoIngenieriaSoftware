from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('etapasJuego', '0018_pitch_score_ai'),
    ]

    operations = [
        migrations.AddField(
            model_name='gamesession',
            name='qr_encuesta_url',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='gamesession',
            name='qr_instagram_url',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='gamesession',
            name='qr_linkedin_url',
            field=models.URLField(blank=True, null=True),
        ),
    ]
