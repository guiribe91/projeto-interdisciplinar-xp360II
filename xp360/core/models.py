from django.db import models
from accounts.models import Usuario

class Turma(models.Model):
    nome = models.CharField(max_length=100)
    serie = models.CharField(max_length=50)
    ano_letivo = models.IntegerField()
    codigo = models.CharField(max_length=10, unique=True)
    professor = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='turmas')

    def __str__(self):
        return f"{self.nome} - {self.serie}"
    
    class Meta:
        verbose_name = "Turma"
        verbose_name_plural = "Turmas"


class Missao(models.Model):
    titulo = models.CharField(max_length=100)
    descricao = models.TextField()
    xp = models.IntegerField()
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE)
    data_criacao = models.DateTimeField(auto_now_add=True)
    disciplina = models.CharField(max_length=100, null=True, blank=True)
    duracao = models.IntegerField(null=True, blank=True)  # em minutos

    def __str__(self):
        return self.titulo
    
    class Meta:
        verbose_name = "Missão"
        verbose_name_plural = "Missões"
        ordering = ['-data_criacao']  # Mais recentes primeiro


class MissaoAluno(models.Model):
    aluno = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    missao = models.ForeignKey(Missao, on_delete=models.CASCADE)
    concluida = models.BooleanField(default=False)
    data_conclusao = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = ('aluno', 'missao')
        verbose_name = "Missão do Aluno"
        verbose_name_plural = "Missões dos Alunos"

    def __str__(self):
        return f"{self.aluno.username} - {self.missao.titulo}"


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