from django.urls import path
from . import views

urlpatterns = [
    path('criar-missao/', views.criar_missao, name='criar_missao'),
    path('concluir-missao/<int:missao_aluno_id>/', views.concluir_missao, name='concluir_missao'),  # ← Mudei para missao_aluno_id
    path('responder/<int:missao_aluno_id>/', views.responder_questao, name='responder_questao'),
]