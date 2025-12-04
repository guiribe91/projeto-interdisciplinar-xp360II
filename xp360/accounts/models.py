from django.db import models
from django.contrib.auth.models import AbstractUser


class Usuario(AbstractUser):
    TIPOS = (
        ('ALUNO', 'Aluno'),
        ('PROFESSOR', 'Professor'),
    )

    tipo = models.CharField(max_length=20, choices=TIPOS)

    # Importante: referência por string para evitar circular import
    turma = models.ForeignKey(
        "core.Turma",
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    # Campos de XP e progressão
    xp_total = models.IntegerField(default=0, verbose_name="XP Total")
    nivel = models.IntegerField(default=1, verbose_name="Nível")

    def __str__(self):
        return f"{self.username} ({self.tipo})"

    def xp_para_proximo_nivel(self):
        """
        Calcula quanto XP falta para o próximo nível.
        Fórmula progressiva: cada nível requer mais XP que o anterior.
        """
        xp_necessario = self.nivel * 100  # 100 XP por nível (ajuste conforme necessário)
        xp_atual_no_nivel = self.xp_total % xp_necessario
        return xp_necessario - xp_atual_no_nivel

    def adicionar_xp(self, quantidade):
        """
        Adiciona XP ao usuário e verifica se subiu de nível.
        Retorna True se subiu de nível, False caso contrário.
        """
        self.xp_total += quantidade
        nivel_anterior = self.nivel
        
        # Calcula o novo nível baseado no XP total
        # Fórmula: nível = raiz quadrada de (xp_total / 100) + 1
        # Isso cria uma progressão onde cada nível fica mais difícil
        self.nivel = int((self.xp_total / 100) ** 0.5) + 1
        
        self.save()
        
        return self.nivel > nivel_anterior  # Retorna True se subiu de nível

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"