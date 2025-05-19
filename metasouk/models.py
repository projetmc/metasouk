from django.db import models
from django.core.files.base import ContentFile
from io import BytesIO
from django.core.files.storage import default_storage

class Utilisateur(models.Model):
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=128)
    email = models.EmailField(null=True, blank=True)
    nom = models.CharField(max_length=100, null=True, blank=True)
    prenom = models.CharField(max_length=100, null=True, blank=True)
    statut = models.CharField(
        max_length=20,
        choices=[
            ('client', 'Client'),
            ('vendeur', 'Vendeur'),
            ('admin', 'Admin')
        ],
        default='client'
    )
    date_joined = models.DateTimeField(auto_now_add=True)
    age = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return f"Utilisateur {self.username}"

class Vendeur(models.Model):
    utilisateur = models.OneToOneField(Utilisateur, on_delete=models.CASCADE, primary_key=True)
    revenu_total = models.FloatField(default=0)

    def __str__(self):
        return f"Vendeur {self.utilisateur.username}"

class Administrateur(models.Model):
    utilisateur = models.OneToOneField(Utilisateur, on_delete=models.CASCADE, primary_key=True)
    idClientApprouveCommeVendeur = models.JSONField(default=list)
    clients_demandant_vente = models.JSONField(default=list)

    def __str__(self):
        return f"Administrateur {self.utilisateur.username}"


class ProduitNFT(models.Model):
    image = models.ImageField(upload_to='nft_images/', default='nft_images/default.jpg') 
    image_data = models.BinaryField(null=True, blank=True)  # Stocker l'image en binaire
    nom = models.CharField(max_length=255)
    description = models.TextField()
    proprietaire = models.ForeignKey('Utilisateur', on_delete=models.CASCADE) 
    prix = models.DecimalField(max_digits=12, decimal_places=2)
    categorie = models.CharField(max_length=50, choices=[('artistique', 'Artistique'), ('musicale', 'Musicale'), ('gaming', 'Gaming')])
    date_creation = models.DateTimeField(auto_now_add=True)
    type = models.CharField(max_length=100, null=True, blank=True)
    certification = models.CharField(max_length=100, null=True, blank=True)
    est_vendu = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.image:
            # Ouvre le fichier image pour récupérer les données binaires
            img_file = self.image.open()
            img_bytes = img_file.read()
            self.image_data = img_bytes  # Stocker les données binaires
        super().save(*args, **kwargs)

    def __str__(self):
        return f"ProduitNFT {self.id}"

class Panier(models.Model):
    utilisateur = models.ForeignKey(Utilisateur, null=True, blank=True, on_delete=models.CASCADE)
    date_mise_a_jour = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Panier {self.id}"
    
    def total_price(self):
        return sum(article.produit.prix for article in self.articles.all())

class ArticlePanier(models.Model):
    panier = models.ForeignKey(Panier, on_delete=models.CASCADE, related_name="articles", default=1)
    produit = models.ForeignKey(ProduitNFT, on_delete=models.CASCADE, default=1)

    def __str__(self):
        return f"{self.produit.nom} dans panier {self.panier.id}"
     
class ArticleCommande(models.Model):
    commande = models.ForeignKey('Commande', on_delete=models.CASCADE, default=1)
    produit = models.ForeignKey('ProduitNFT', on_delete=models.CASCADE,  default=1)
    prix_achat = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"ArticleCommande {self.id}"

class Commande(models.Model):
    utilisateur = models.ForeignKey('Utilisateur', on_delete=models.CASCADE, related_name='commandes')
    date_creation = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(max_length=20, default='en_attente')
    montant_total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Commande {self.id}"


class Paiement(models.Model):
    commande_id = models.IntegerField()
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    methode_paiement = models.CharField(max_length=50)
    statut = models.CharField(max_length=20, choices=[('effectuee', 'Effectuée'), ('en_attente', 'En attente')], null=True)
    date_paiement = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Paiement {self.id}"

class Transaction(models.Model):
    acheteur = models.ForeignKey('Utilisateur', related_name='transactions_acheteur', null=True, blank=True, on_delete=models.SET_NULL)
    vendeur = models.ForeignKey('Utilisateur', related_name='transactions_vendeur', null=True, blank=True, on_delete=models.SET_NULL)
    commande = models.ForeignKey('Commande', null=True, blank=True, on_delete=models.SET_NULL)
    montant = models.FloatField()
    statut = models.CharField(
        max_length=20,
        choices=[
            ('validee', 'Validée'),
            ('refusee', 'Refusée'),
            ('en_attente', 'En attente')
        ]
    )

    def __str__(self):
        return f"Transaction {self.id}"

class TransactionPaiement(models.Model):
    transaction_id = models.IntegerField()
    paiement_id = models.IntegerField()

    def __str__(self):
        return f"TransactionPaiement {self.id}"
    
class Commentaire(models.Model):
    auteur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE)
    produit = models.ForeignKey(ProduitNFT, on_delete=models.CASCADE, related_name="commentaires")
    contenu = models.TextField()
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Commentaire de {self.auteur.username} sur {self.produit.nom}"

class Evaluation(models.Model):
    auteur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE)
    produit = models.ForeignKey(ProduitNFT, on_delete=models.CASCADE, related_name="evaluations")
    note = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    date_evaluation = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('auteur', 'produit')  # Un utilisateur ne peut évaluer qu'une seule fois

    def __str__(self):
        return f"Évaluation de {self.auteur.username} - {self.note} étoiles"

class Signalement(models.Model):
    signalant = models.ForeignKey(Utilisateur, on_delete=models.CASCADE)
    produit = models.ForeignKey(ProduitNFT, on_delete=models.CASCADE, related_name="signalements")
    motif = models.TextField()
    date_signalement = models.DateTimeField(auto_now_add=True)
    traite = models.BooleanField(default=False)

    def __str__(self):
        return f"Signalement de {self.signalant.username} pour {self.produit.nom}"
