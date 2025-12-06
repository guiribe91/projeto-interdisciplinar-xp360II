from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import date, timedelta


class Usuario(AbstractUser):
    TIPO_CHOICES = [
        ('ALUNO', 'Aluno'),
        ('PROFESSOR', 'Professor'),
    ]

    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, default='ALUNO')
    turma = models.ForeignKey(
        'core.Turma',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    # Sistema de XP e Níveis
    xp_total = models.IntegerField(default=0)
    nivel = models.IntegerField(default=1)
    
    # 🔥 NOVO: Sistema de Streak
    streak_atual = models.IntegerField(default=0)
    melhor_streak = models.IntegerField(default=0)
    ultimo_acesso = models.DateField(null=True, blank=True)
    ultima_missao_concluida = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"

    def __str__(self):
        return f"{self.username} ({self.get_tipo_display()})"

    def adicionar_xp(self, xp):
        """Adiciona XP e verifica se subiu de nível"""
        self.xp_total += xp
        
        # Sistema de níveis progressivo
        nivel_anterior = self.nivel
        self.nivel = (self.xp_total // 100) + 1
        
        self.save()
        
        # Retorna True se subiu de nível
        return self.nivel > nivel_anterior

    def xp_para_proximo_nivel(self):
        """Calcula quanto XP falta para o próximo nível"""
        xp_proximo_nivel = self.nivel * 100
        return xp_proximo_nivel - self.xp_total

    def progresso_nivel(self):
        """Retorna o progresso percentual no nível atual"""
        xp_nivel_atual = (self.nivel - 1) * 100
        xp_proximo_nivel = self.nivel * 100
        xp_no_nivel = self.xp_total - xp_nivel_atual
        total_xp_nivel = xp_proximo_nivel - xp_nivel_atual
        
        if total_xp_nivel == 0:
            return 100
        
        return int((xp_no_nivel / total_xp_nivel) * 100)

    # 🔥 NOVO: Métodos de Streak
    def atualizar_streak(self):
        """Atualiza o streak baseado no último acesso"""
        hoje = date.today()
        
        # Primeiro acesso
        if not self.ultimo_acesso:
            self.streak_atual = 1
            self.ultimo_acesso = hoje
            self.save()
            return
        
        # Já acessou hoje - não faz nada
        if self.ultimo_acesso == hoje:
            return
        
        # Acessou ontem - incrementa streak
        if self.ultimo_acesso == hoje - timedelta(days=1):
            self.streak_atual += 1
            if self.streak_atual > self.melhor_streak:
                self.melhor_streak = self.streak_atual
        
        # Perdeu o streak (mais de 1 dia sem acessar)
        elif self.ultimo_acesso < hoje - timedelta(days=1):
            self.streak_atual = 1
        
        self.ultimo_acesso = hoje
        self.save()

    def atualizar_streak_missao(self):
        """Atualiza streak quando completa uma missão"""
        hoje = date.today()
        
        # Primeira missão
        if not self.ultima_missao_concluida:
            self.streak_atual = 1
            self.ultima_missao_concluida = hoje
            self.save()
            return
        
        # Já completou missão hoje
        if self.ultima_missao_concluida == hoje:
            return
        
        # Completou missão ontem - incrementa
        if self.ultima_missao_concluida == hoje - timedelta(days=1):
            self.streak_atual += 1
            if self.streak_atual > self.melhor_streak:
                self.melhor_streak = self.streak_atual
        
        # Perdeu o streak
        elif self.ultima_missao_concluida < hoje - timedelta(days=1):
            self.streak_atual = 1
        
        self.ultima_missao_concluida = hoje
        self.save()

    def get_titulo_streak(self):
        """Retorna título baseado no streak"""
        if self.streak_atual >= 100:
            return "🔥 Lendário"
        elif self.streak_atual >= 30:
            return "⭐ Dedicado"
        elif self.streak_atual >= 7:
            return "💪 Consistente"
        elif self.streak_atual >= 3:
            return "📚 Estudioso"
        else:
            return "🌱 Iniciante"