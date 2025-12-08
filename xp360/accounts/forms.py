# accounts/forms.py

from django import forms
from .models import Usuario

class CadastroAlunoForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    password_confirm = forms.CharField(widget=forms.PasswordInput, label="Confirmar Senha")
    
    # NOVO: Campo de aceite dos termos
    aceito_termos = forms.BooleanField(
        required=True,
        label='',
        error_messages={'required': 'Você deve aceitar os termos para se cadastrar'}
    )
    
    class Meta:
        model = Usuario
        fields = ['username', 'email', 'data_nascimento', 'serie', 'password']
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password != password_confirm:
            raise forms.ValidationError("As senhas não coincidem")
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class CadastroProfessorForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    password_confirm = forms.CharField(widget=forms.PasswordInput, label="Confirmar Senha")
    
    # NOVO: Campo de aceite dos termos
    aceito_termos = forms.BooleanField(
        required=True,
        label='',
        error_messages={'required': 'Você deve aceitar os termos para se cadastrar'}
    )
    
    class Meta:
        model = Usuario
        fields = ['username', 'email', 'password']
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password != password_confirm:
            raise forms.ValidationError("As senhas não coincidem")
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user
