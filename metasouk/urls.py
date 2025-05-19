from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    # acceuil
    path('', views.index, name='index'),
    
    #paiement 
    path('paiement/', views.paiement_view, name='paiement'),
    path('creer_commande/', views.creer_commande, name='creer_commande'),
    
    # panier
    path('ajouter-au-panier/<int:produit_id>/', views.ajouter_au_panier, name='ajouter_au_panier'),
    path('panier/supprimer/<int:article_id>/', views.retirer_du_panier, name='retirer_du_panier'),
    path('panier/', views.panier_view, name='panier'),
    
    # connexion / inscritption / deconnexion
    path('signin/', views.signin_view, name='signin'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),

    # produit 
    path('products/', views.products_view, name='products'),
    path('prod/<int:id>/', views.prod_view, name='prod'),
    
    #client
    path('client/', views.client_view, name='client'),
    path('Becomeseller/', views.Becomeseller_view, name='Becomeseller'),
    path('delete-account/', views.delete_account, name='delete_account'),
    
    #vendeur
    path('vendeur/', views.vendeur_view, name='vendeur'),
    path('produit/modifier/', views.modifier_produit, name='modifier_produit'),
    path('produit/supprimer/<int:produit_id>/', views.supprimer_produit, name='supprimer_produit'),
    
    #admin
    path('adminm/', views.admin_view, name='adminm'),
    path('adminm/edit_product/', views.edit_product, name='edit_product'), 
    path('adminm/delete_product/<int:id>/', views.delete_product, name='delete_product'),
    path('adminm/accepter/<int:user_id>/', views.accepter_demande_vendeur, name='accepter_demande'),
    path('adminm/refuser/<int:user_id>/', views.refuser_demande_vendeur, name='refuser_demande'),

   
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)