from django.db import models
from django.utils import timezone


# ==========================================
# 🆕 NOVO: Model de Disciplina
# ==========================================
class Disciplina(models.Model):
    nome = models.CharField(max_length=100)
    icone = models.CharField(max_length=10)  # emoji
    cor = models.CharField(max_length=7, default='#667eea')     # hex color (#FF6B6B)
    
    class Meta:
        verbose_name = "Disciplina"
        verbose_name_plural = "Disciplinas"
        ordering = ['nome']
    
    def __str__(self):
        return f"{self.icone} {self.nome}"


# ==========================================
# Turma - CORRIGIDO com referência string
# ==========================================
class Turma(models.Model):
    nome = models.CharField(max_length=100)
    serie = models.CharField(max_length=50)
    ano_letivo = models.IntegerField()
    professor = models.ForeignKey(
        'accounts.Usuario',
        on_delete=models.CASCADE,
        related_name='turmas_professor',  # ← MUDANÇA: de 'turmas' para 'turmas_professor'
        limit_choices_to={'tipo': 'PROFESSOR'}
    )
    data_criacao = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    
    class Meta:
        verbose_name = 'Turma'
        verbose_name_plural = 'Turmas'
        ordering = ['-ano_letivo', 'nome']
    
    def __str__(self):
        return f"{self.nome} - {self.serie} ({self.ano_letivo})"


# ==========================================
# 🔄 ATUALIZADO: Missao agora tem disciplina e tipo
# ==========================================
class Missao(models.Model):
    TIPO_CHOICES = [
        ('QUESTAO', 'Questão com Alternativas'),
        ('TAREFA', 'Tarefa Livre'),
    ]
    
    titulo = models.CharField(max_length=100)
    descricao = models.TextField()
    xp = models.IntegerField()
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_disponivel = models.DateField(default=timezone.now)
    
    # 🆕 NOVO: Campos atualizados
    disciplina = models.ForeignKey(
        Disciplina, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    tipo = models.CharField(
        max_length=20, 
        choices=TIPO_CHOICES, 
        default='TAREFA'
    )
    duracao = models.IntegerField(null=True, blank=True, help_text="Duração em minutos")

    def __str__(self):
        return self.titulo
    
    class Meta:
        verbose_name = "Missão"
        verbose_name_plural = "Missões"
        ordering = ['-data_criacao']


# ==========================================
# 🆕 NOVO: Model de Alternativa
# ==========================================
class Alternativa(models.Model):
    ORDEM_CHOICES = [
        ('A', 'Alternativa A'),
        ('B', 'Alternativa B'),
        ('C', 'Alternativa C'),
        ('D', 'Alternativa D'),
    ]
    
    missao = models.ForeignKey(
        Missao, 
        on_delete=models.CASCADE, 
        related_name='alternativas'
    )
    texto = models.CharField(max_length=500)
    ordem = models.CharField(max_length=1, choices=ORDEM_CHOICES)
    correta = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Alternativa"
        verbose_name_plural = "Alternativas"
        ordering = ['ordem']
        unique_together = ('missao', 'ordem')  # Evita duplicar A, B, C, D
    
    def __str__(self):
        check = "✓" if self.correta else "✗"
        return f"{self.ordem}) {self.texto[:50]} {check}"


# ==========================================
# MissaoAluno
# ==========================================
class MissaoAluno(models.Model):
    aluno = models.ForeignKey("accounts.Usuario", on_delete=models.CASCADE)
    missao = models.ForeignKey(Missao, on_delete=models.CASCADE)
    concluida = models.BooleanField(default=False)
    data_conclusao = models.DateField(null=True, blank=True)
    
    # 🆕 NOVO: Para questões com alternativas
    resposta_escolhida = models.CharField(
        max_length=1, 
        null=True, 
        blank=True,
        choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')]
    )
    acertou = models.BooleanField(default=False)

    class Meta:
        unique_together = ('aluno', 'missao')
        verbose_name = "Missão do Aluno"
        verbose_name_plural = "Missões dos Alunos"

    def __str__(self):
        return f"{self.aluno.username} - {self.missao.titulo}"


# ==========================================
# Badge
# ==========================================
class Badge(models.Model):
    nome = models.CharField(max_length=50)
    descricao = models.CharField(max_length=200)
    icone = models.CharField(max_length=100)
    condicao = models.CharField(max_length=200)

    def __str__(self):
        return self.nome
    
    class Meta:
        verbose_name = "Badge"
        verbose_name_plural = "Badges"


# ==========================================
# BadgeUsuario
# ==========================================
class BadgeUsuario(models.Model):
    usuario = models.ForeignKey("accounts.Usuario", on_delete=models.CASCADE)
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    data_conquista = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("usuario", "badge")
        verbose_name = "Badge Conquistada"
        verbose_name_plural = "Badges Conquistadas"

    def __str__(self):
        return f"{self.usuario.username} conquistou {self.badge.nome}"
