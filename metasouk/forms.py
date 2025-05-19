from django import forms
from .models import Utilisateur

class InscriptionForm(forms.ModelForm):
    class Meta:
        model = Utilisateur
        fields = ['username', 'password', 'email', 'statut', 'age']

    # Vous pouvez ajouter une validation personnalisée ici
    def clean_password(self):
        password = self.cleaned_data.get('password')
        # Ajoutez des règles de validation pour le mot de passe ici si nécessaire
        return password
