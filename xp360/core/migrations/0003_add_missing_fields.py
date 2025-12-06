from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_alter_badge_options_alter_missao_options_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                ALTER TABLE core_missao 
                ADD COLUMN IF NOT EXISTS data_disponivel DATE;
                
                ALTER TABLE core_missao 
                ADD COLUMN IF NOT EXISTS duracao INTEGER;
            """,
            reverse_sql="""
                ALTER TABLE core_missao DROP COLUMN IF EXISTS data_disponivel;
                ALTER TABLE core_missao DROP COLUMN IF EXISTS duracao;
            """
        ),
    ]