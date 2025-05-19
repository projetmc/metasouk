from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Utilisateur, ProduitNFT, Panier, ArticlePanier, ArticleCommande, Commande, Paiement, Transaction, TransactionPaiement, Vendeur, Administrateur, Commentaire, Evaluation, Signalement
from django.contrib.auth.hashers import make_password , check_password
from .forms import InscriptionForm
from django.contrib.auth import logout
from functools import wraps
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required
from PIL import Image
from django.db.models import Sum
from django.contrib.auth import login as auth_login
from django.urls import reverse
from django.db.models import Prefetch
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.views.decorators.http import require_POST
from django.db import transaction
from django.db.models import Avg

# vue acceuil
def index(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')

        subject = f"Nouveau message de contact de {name}"
        message_body = f"Nom: {name}\nEmail: {email}\n\nMessage:\n{message}"

        send_mail(
            subject,
            message_body,
            settings.EMAIL_HOST_USER,  
            [settings.EMAIL_HOST_USER],  
            fail_silently=False,
        )
        return render(request, 'metasouk/index.html', {'success': True})

    return render(request, 'metasouk/index.html')

# vue connexion
def signin_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            # Récupérer l'utilisateur
            user = Utilisateur.objects.get(username=username)

            # Vérifier le mot de passe
            if check_password(password, user.password):
                request.session['user_id'] = user.id
                request.session['user_statut'] = user.statut

                # Redirection selon le statut
                if user.statut == 'client':
                    return redirect('client')  
                elif user.statut == 'vendeur':
                    return redirect('client')
                elif user.statut == 'admin':
                    return redirect('adminm')
                else:
                    messages.error(request, "Statut utilisateur inconnu.")
                    return redirect('signin')
            else:
                messages.error(request, "Nom d'utilisateur ou mot de passe incorrect.")
                return redirect('signin')

        except Utilisateur.DoesNotExist:
            messages.error(request, "Nom d'utilisateur ou mot de passe incorrect.")
            return redirect('signin')

    return render(request, 'metasouk/signin.html')

# vue deconnexion
def logout_view(request):
    logout(request)  
    request.session.flush()
    return redirect('signin')  

# vue de inscription
def signup_view(request):
    if request.method == "POST":
        prenom = request.POST.get('name-1')
        nom = request.POST.get('name-2')
        email = request.POST.get('email')
        username = request.POST.get('username')
        password = make_password(request.POST.get('text-1'))
        age = request.POST.get('text')

        if prenom and nom and email and username and password and age:
            utilisateur = Utilisateur.objects.create(
                username=username,
                password=password,
                email=email,
                nom=nom,
                prenom=prenom,
                age=age,
                statut='client'
            )

            # Envoi de l'email de bienvenue
            try:
                send_mail(
                    subject='Bienvenue sur MetaSouk !',
                    message=f"Bonjour {prenom},\n\nBienvenue sur MetaSouk ! Nous sommes ravis de vous compter parmi nous.\n\nExplorez, achetez et vendez des NFT dès maintenant !",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
            except Exception as e:
                print("Erreur lors de l'envoi de l'email :", e)

            # Connexion automatique
            user = authenticate(request, username=username, password=request.POST.get('text-1'))
            if user is not None:
                login(request, user)
                request.session['user_id'] = user.id
                request.session['user_role'] = user.statut

                messages.success(request, "Inscription réussie !")
                return redirect('index')
            else:
                messages.error(request, "Erreur de connexion après l'inscription.")
                return redirect('signin')

        else:
            messages.error(request, "Tous les champs sont obligatoires.")
            return render(request, 'metasouk/signup.html')

    # Affichage des statistiques
    client_count = Utilisateur.objects.filter(statut='client').count()
    vendeur_count = Utilisateur.objects.filter(statut='vendeur').count()
    product_count = ProduitNFT.objects.count()

    return render(request, 'metasouk/signup.html', {
        'client_count': client_count,
        'vendeur_count': vendeur_count,
        'product_count': product_count,
    })

# les sessions 
def session_required(role=None):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user_id = request.session.get('user_id')
            user_statut = request.session.get('user_statut')

            if not user_id or (role and user_statut != role):
                messages.error(request, "Vous n'avez pas accès à cette page.")
                return redirect('signin')  # Redirige vers la page de connexion
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

# vue produit
def products_view(request):
    categorie = request.GET.get('categorie')
    search = request.GET.get('search')

    produits = ProduitNFT.objects.filter(est_vendu=False)

    if categorie:
        produits = produits.filter(categorie=categorie)

    if search:
        produits = produits.filter(nom__icontains=search)  # Recherche alphabétique insensible à la casse

    return render(request, 'metasouk/products.html', {
        'produits': produits,
        'selected_categorie': categorie,
        'search_query': search,
    })

# vue produit detaillé
def prod_view(request, id):
    produit = get_object_or_404(ProduitNFT, id=id)
    commentaires = Commentaire.objects.filter(produit=produit).order_by('-date_creation')

    utilisateur_id = request.session.get('user_id')
    evaluation_utilisateur = None  # par défaut pas d'évaluation visible

    if utilisateur_id:
        auteur = get_object_or_404(Utilisateur, id=utilisateur_id)
        # Chercher si l'utilisateur a déjà évalué ce produit
        evaluation = Evaluation.objects.filter(auteur=auteur, produit=produit).first()
        if evaluation:
            evaluation_utilisateur = evaluation.note

    if request.method == 'POST':
        # Vérification de connexion
        if not utilisateur_id:
            messages.warning(request, "Vous devez être connecté pour effectuer cette action.")
            login_url = f"{reverse('signin')}?next={request.path}"
            return redirect(login_url)

        auteur = get_object_or_404(Utilisateur, id=utilisateur_id)
        action_type = request.POST.get('action_type')

        # Signalement
        if action_type == 'signaler':
            motifs = request.POST.getlist('reason')
            autre = request.POST.get('autre', '').strip()
            motif_complet = ", ".join(motifs)
            if autre:
                motif_complet += f". Autre : {autre}"

            if motif_complet:
                Signalement.objects.create(
                    signalant=auteur,
                    produit=produit,
                    motif=motif_complet
                )
                messages.success(request, "Votre signalement a été transmis. Merci !")
            return redirect('prod', id=produit.id)

        # Évaluation
        elif action_type == 'evaluer':
            note_str = request.POST.get('note', '')
            if note_str.isdigit():
                note = int(note_str)
                if 1 <= note <= 5:
                    Evaluation.objects.update_or_create(
                        auteur=auteur,
                        produit=produit,
                        defaults={'note': note}
                    )
                    messages.success(request, "Votre évaluation a été prise en compte.")
                else:
                    messages.warning(request, "Note invalide.")
            else:
                messages.warning(request, "Note invalide ou non fournie.")
            return redirect('prod', id=produit.id)

        # Commentaire
        else:
            contenu = request.POST.get('contenu')
            if contenu:
                Commentaire.objects.create(auteur=auteur, produit=produit, contenu=contenu)
                messages.success(request, "Commentaire ajouté.")
            return redirect('prod', id=produit.id)

    return render(request, 'metasouk/prod.html', {
        'produit': produit,
        'commentaires': commentaires,
        'evaluation_utilisateur': evaluation_utilisateur,
    })

# vue client 
def client_view(request):
    utilisateur_id = request.session.get('user_id')

    if not utilisateur_id:
        return redirect('signin')

    utilisateur = Utilisateur.objects.get(id=utilisateur_id)

    if request.method == 'POST':
        utilisateur.nom = request.POST.get('nom')
        utilisateur.prenom = request.POST.get('prenom')
        utilisateur.username = request.POST.get('username')
        utilisateur.email = request.POST.get('email')
        utilisateur.age = request.POST.get('age')
        utilisateur.statut = request.POST.get('status')
        utilisateur.save()
        messages.success(request, "Informations mises à jour avec succès.")
        return redirect('client')

    # Récupérer tous les produits achetés par l'utilisateur
    commandes = Commande.objects.filter(utilisateur_id=utilisateur_id)
    article_commandes = ArticleCommande.objects.filter(commande_id__in=commandes)
    produits_achetes = ProduitNFT.objects.filter(id__in=[article.produit_id for article in article_commandes])

    return render(request, 'metasouk/client.html', {
        'utilisateur': utilisateur,
        'produits_achetes': produits_achetes
    })

#Supprimer un compte 
def delete_account(request):
    utilisateur_id = request.session.get('user_id')

    if not utilisateur_id:
        return redirect('signin')

    utilisateur = Utilisateur.objects.get(id=utilisateur_id)

    # On récupère l'email avant suppression
    email_utilisateur = utilisateur.email

    # Envoi de l'email
    send_mail(
        subject="Confirmation de suppression de compte",
        message="Bonjour,\n\nVotre compte a bien été supprimé de notre plateforme. "
                "Si vous n'êtes pas à l'origine de cette suppression, veuillez nous contacter.\n\nCordialement,\nL'équipe.",
        from_email=None,  # Utilise DEFAULT_FROM_EMAIL
        recipient_list=[email_utilisateur],
        fail_silently=False,
    )

    # Suppression de l'utilisateur et déconnexion
    utilisateur.delete()
    request.session.flush()

    messages.success(request, "Compte supprimé avec succès. Un email de confirmation vous a été envoyé.")
    return redirect('index')

# devenir vendeur
def Becomeseller_view(request):
    utilisateur_id = request.session.get('user_id')

    if not utilisateur_id:
        messages.error(request, "Vous devez être connecté pour faire une demande.")
        return redirect('signin')

    utilisateur = Utilisateur.objects.get(id=utilisateur_id)

    if utilisateur.statut != 'client':
        messages.error(request, "Seuls les clients peuvent faire une demande pour devenir vendeur.")
        return redirect('client')

    if request.method == 'POST':
        email = request.POST.get('email')
        name = request.POST.get('name')

        sujet = "Demande pour devenir vendeur"
        message = f"Nom : {name}\nEmail : {email}\nID utilisateur : {utilisateur.id}\nSouhaite devenir vendeur."
        destinataires = ['projetmc704@gmail.com']
        expediteur = 'projetmc704@gmail.com'
        try:
            # Ajouter l'ID du client dans la liste des demandes
            admin = Administrateur.objects.first()
            if admin:
                demandes = admin.clients_demandant_vente
                if utilisateur.id not in demandes:
                    demandes.append(utilisateur.id)
                    admin.clients_demandant_vente = demandes
                    admin.save()

            # Envoyer un email aussi
            send_mail(sujet, message, expediteur, destinataires, fail_silently=False)
            messages.success(request, "Votre demande a été envoyée avec succès.")
            return redirect('client')
        except Exception as e:
            messages.error(request, f"Une erreur est survenue : {str(e)}")

    return render(request, 'metasouk/Becomeseller.html')

# vue vendeur
@session_required(role='vendeur')
def vendeur_view(request):
    utilisateur_id = request.session.get('user_id')
    utilisateur = Utilisateur.objects.get(id=utilisateur_id)

    if utilisateur.statut != 'vendeur':
        messages.error(request, 'Vous devez être un vendeur pour accéder à cette page.')
        return redirect('accueil')

    if request.method == 'POST':
        nom = request.POST.get('nom')
        description = request.POST.get('description')
        prix = request.POST.get('prix')
        categorie = request.POST.get('categorie')
        type = request.POST.get('type')
        certification = request.POST.get('certification')
        image = request.FILES.get('image')

        if image:
            try:
                img = Image.open(image)
                if img.format not in ['JPEG', 'PNG']:
                    messages.error(request, 'Seuls les fichiers JPEG et PNG sont autorisés.')
                    return redirect('vendeur')
            except Exception:
                messages.error(request, 'Image invalide.')
                return redirect('vendeur')

        produit = ProduitNFT(
            nom=nom,
            description=description,
            prix=prix,
            categorie=categorie,
            type=type,
            certification=certification,
            image=image,
            proprietaire=utilisateur
        )
        produit.save()
        messages.success(request, 'Produit ajouté avec succès.')
        return redirect('vendeur')

    produits_en_vente = ProduitNFT.objects.filter(proprietaire=utilisateur, est_vendu=False)
    transactions = Transaction.objects.filter(vendeur=utilisateur, statut='validee').select_related('commande')
    commandes_ids = [transaction.commande.id for transaction in transactions]

    articles = ArticleCommande.objects.filter(commande_id__in=commandes_ids).select_related('produit')
    revenu_total = articles.aggregate(total=Sum('prix_achat'))['total'] or 0

    produits_vendus = [{'nom': article.produit.nom, 'image_url': article.produit.image.url, 'prix': article.prix_achat} for article in articles]

    return render(request, 'metasouk/vendeur.html', {
        'produits_en_vente': produits_en_vente,
        'produits_vendus': produits_vendus,
        'revenu_total': revenu_total,
    })

# modifier un produit pour vendeur 
def modifier_produit(request):
    if request.method == "POST":
        produit_id = request.POST.get('produit_id')
        produit = get_object_or_404(ProduitNFT, id=produit_id)

        # Mise à jour des informations du produit
        produit.nom = request.POST.get('nom')
        produit.description = request.POST.get('description')
        produit.prix = request.POST.get('prix')
        produit.type = request.POST.get('type')
        produit.categorie = request.POST.get('categorie')
        produit.certification = request.POST.get('certification')

        if request.FILES.get('image'):
            produit.image = request.FILES.get('image')

        produit.save()

        messages.success(request, 'Produit modifié avec succès.')
        return redirect('vendeur')  # Redirige vers la page vendeur

    return redirect('vendeur')

# supprimer un produit pour vendeur
def supprimer_produit(request, produit_id):
    produit = get_object_or_404(ProduitNFT, id=produit_id)
    produit.delete()
    messages.success(request, 'Produit supprimé avec succès.')
    return redirect('vendeur')  # Redirige vers la page vendeur après suppression

#vue admin 
def admin_view(request):
    utilisateur_id = request.session.get('user_id')
    utilisateur = get_object_or_404(Utilisateur, id=utilisateur_id)

    if utilisateur.statut != 'admin':
        messages.error(request, 'Accès refusé. Vous n\'êtes pas administrateur.')
        return redirect('signin')

    admin_record, created = Administrateur.objects.get_or_create(utilisateur=utilisateur)

    admin_record.clients_demandant_vente = [
        uid for uid in admin_record.clients_demandant_vente
        if Utilisateur.objects.filter(id=uid, statut='client').exists()
    ]
    admin_record.save()

    produits_vendeurs = ProduitNFT.objects.filter(proprietaire__statut='vendeur')
    produits_admin = ProduitNFT.objects.filter(proprietaire=utilisateur)

    clients = Utilisateur.objects.filter(statut='client')
    vendeurs = Utilisateur.objects.filter(statut='vendeur')

    commandes = Commande.objects.select_related('utilisateur').prefetch_related(
        Prefetch('articlecommande_set', queryset=ArticleCommande.objects.select_related('produit'))
    )

    clients_demandant_vente = Utilisateur.objects.filter(
        id__in=admin_record.clients_demandant_vente,
        statut='client'
    )

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_admin':
            utilisateur.username = request.POST.get('username')
            utilisateur.email = request.POST.get('email')
            utilisateur.age = request.POST.get('age')
            utilisateur.save()
            messages.success(request, 'Informations mises à jour avec succès.')
            return redirect('adminm')

        elif action == 'add_product':
            nom = request.POST.get('nom')
            description = request.POST.get('description')
            prix = request.POST.get('prix')
            categorie = request.POST.get('categorie')
            type_ = request.POST.get('type')
            certification = request.POST.get('certification')
            image = request.FILES.get('image')

            if image:
                try:
                    img = Image.open(image)
                    if img.format not in ['JPEG', 'PNG']:
                        messages.error(request, 'Seuls les fichiers JPEG et PNG sont autorisés.')
                        return redirect('adminm')
                except Exception:
                    messages.error(request, 'Image invalide.')
                    return redirect('adminm')

            produit = ProduitNFT(
                nom=nom,
                description=description,
                prix=prix,
                categorie=categorie,
                type=type_,
                certification=certification,
                image=image,
                proprietaire=utilisateur
            )
            produit.save()
            messages.success(request, 'Produit ajouté avec succès.')
            return redirect('adminm')

        # Suppression de la gestion du statut de la commande ici
        # Plus aucune modification du statut de commande via l'admin

    return render(request, 'metasouk/adminm.html', {
        'utilisateur': utilisateur,
        'produits_admin': produits_admin,
        'produits_vendeurs': produits_vendeurs,
        'clients': clients,
        'vendeurs': vendeurs,
        'commandes': commandes,
        'clients_demandant_vente': clients_demandant_vente
    })

# vue accepter client de devenir vendeur
def accepter_demande_vendeur(request, user_id):
    utilisateur = get_object_or_404(Utilisateur, id=user_id)

    if utilisateur.statut != 'client':
        messages.error(request, "L'utilisateur n'est pas un client.")
        return redirect('adminm')

    utilisateur.statut = 'vendeur'
    utilisateur.save()

    # Mise à jour dans la liste de l’admin
    admin = Administrateur.objects.get(utilisateur__statut='admin')
    if utilisateur.id in admin.clients_demandant_vente:
        admin.clients_demandant_vente.remove(utilisateur.id)
        admin.idClientApprouveCommeVendeur.append(utilisateur.id)
        admin.save()

    # Envoi de mail
    send_mail(
        'Demande acceptée',
        'Félicitations ! Votre demande pour devenir vendeur a été acceptée.',
        settings.DEFAULT_FROM_EMAIL,
        [utilisateur.email],
        fail_silently=True
    )

    messages.success(request, f'{utilisateur.username} est maintenant vendeur.')
    return redirect('adminm')

# vue refuser client de venir vendeur 
def refuser_demande_vendeur(request, user_id):
    utilisateur = get_object_or_404(Utilisateur, id=user_id)

    if utilisateur.statut != 'client':
        messages.warning(request, "L'utilisateur n'est pas un client.")
        return redirect('adminm')

    # Mise à jour dans la liste de l’admin
    admin = Administrateur.objects.get(utilisateur__statut='admin')
    if utilisateur.id in admin.clients_demandant_vente:
        admin.clients_demandant_vente.remove(utilisateur.id)
        admin.save()

    # Envoi de mail
    send_mail(
        'Demande refusée',
        'Votre demande pour devenir vendeur a été refusée.',
        settings.DEFAULT_FROM_EMAIL,
        [utilisateur.email],
        fail_silently=True
    )

    messages.info(request, f'Demande de {utilisateur.username} refusée.')
    return redirect('adminm')

# modifier produit admin   
def edit_product(request):
    if request.method == 'POST':
        produit_id = request.POST.get('produit_id')
        produit = get_object_or_404(ProduitNFT, id=produit_id)
        
        # Mise à jour des informations du produit
        produit.nom = request.POST.get('nom')
        produit.description = request.POST.get('description')
        produit.prix = request.POST.get('prix')
        produit.categorie = request.POST.get('categorie')
        produit.type = request.POST.get('type')
        produit.certification = request.POST.get('certification')
        
        # Mise à jour de l'image si un nouveau fichier est téléchargé
        if request.FILES.get('image'):
            produit.image = request.FILES.get('image')

        produit.save()
        messages.success(request, 'Produit mis à jour avec succès.')
        return redirect('adminm')  

    return redirect('adminm')  

# supprimer produit amdin
def delete_product(request, id):
    produit = get_object_or_404(ProduitNFT, id=id)
    
    # Vérifier si l'utilisateur est un administrateur
    utilisateur_id = request.session.get('user_id')
    utilisateur = get_object_or_404(Utilisateur, id=utilisateur_id)

    if utilisateur.statut != 'admin':
        messages.error(request, 'Accès refusé. Vous n\'êtes pas administrateur.')
        return redirect('signin')

    produit.delete()
    messages.success(request, 'Produit supprimé avec succès.')
    return redirect('adminm')  

# Afficher le panier
def panier_view(request):
    panier = get_or_create_panier(request)
    articles = panier.articles.select_related('produit')
    total = sum(article.produit.prix for article in articles)
    return render(request, 'metasouk/panier.html', {
        'panier': panier,
        'articles': articles,
        'total': total,
    })
    
# creation du panier 
def get_or_create_panier(request):
    user_id = request.session.get('user_id')
    utilisateur = None
    if user_id:
        try:
            utilisateur = Utilisateur.objects.get(id=user_id)
        except Utilisateur.DoesNotExist:
            pass

    if utilisateur:
        panier_id = request.session.get('panier_id')
        if panier_id:
            panier_anonyme = Panier.objects.filter(id=panier_id, utilisateur=None).first()
            if panier_anonyme:
                panier_anonyme.utilisateur = utilisateur
                panier_anonyme.save()
                return panier_anonyme

        panier, _ = Panier.objects.get_or_create(utilisateur=utilisateur)
        return panier

    # utilisateur non connecté
    panier_id = request.session.get('panier_id')
    if panier_id:
        panier = Panier.objects.filter(id=panier_id, utilisateur=None).first()
        if not panier:
            panier = Panier.objects.create(utilisateur=None)
            request.session['panier_id'] = panier.id
    else:
        panier = Panier.objects.create(utilisateur=None)
        request.session['panier_id'] = panier.id
    return panier

# Ajouter un produit au panier
@require_POST
def ajouter_au_panier(request, produit_id):
    print('je suis rentrer')  # Pour debug
    panier = get_or_create_panier(request)
    produit = get_object_or_404(ProduitNFT, id=produit_id)
    article, created = ArticlePanier.objects.get_or_create(panier=panier, produit=produit)
    if created:
        messages.success(request, "Produit ajouté au panier.")
    else:
        messages.info(request, "Produit déjà dans le panier.")
    return redirect('panier')  # redirection vers le panier ici


# Retirer un produit du panier
def retirer_du_panier(request, article_id):
    article = get_object_or_404(ArticlePanier, id=article_id)
    article.delete()
    messages.success(request, "Produit retiré du panier.")
    return redirect('panier')


#vue creer commande
def creer_commande(request):
    if 'user_id' not in request.session:
        return redirect('signin')  # ou la page de login que tu utilises

    utilisateur = get_object_or_404(Utilisateur, id=request.session.get('user_id'))

    # Vérifier s'il existe déjà une commande en attente
    commande = Commande.objects.filter(utilisateur=utilisateur, statut='en_attente').first()
    if commande:
        return redirect('paiement')

    panier = Panier.objects.filter(utilisateur=utilisateur).first()
    if not panier or panier.articles.count() == 0:
        messages.error(request, "Votre panier est vide.")
        return redirect('panier')

    with transaction.atomic():
        montant_total = sum(article.produit.prix for article in panier.articles.all())

        commande = Commande.objects.create(
            utilisateur=utilisateur,
            statut='en_attente',
            montant_total=montant_total
        )

        for article in panier.articles.all():
            ArticleCommande.objects.create(
                commande=commande,
                produit=article.produit,
                prix_achat=article.produit.prix
            )

        panier.articles.all().delete()

    return redirect('paiement')

#vue de paiement 
def paiement_view(request):
    if 'user_id' not in request.session:
        return redirect('signin')

    utilisateur = get_object_or_404(Utilisateur, id=request.session.get('user_id'))
    commande = Commande.objects.filter(utilisateur=utilisateur, statut='en_attente').order_by('-id').first()

    if not commande:
        messages.warning(request, "Aucune commande en attente à payer.")
        return redirect('client')

    if request.method == 'POST':
        with transaction.atomic():
            # Marquer tous les produits comme vendus
            for article in commande.articlecommande_set.all():
                produit = article.produit
                produit.est_vendu = True
                produit.save()

            # Mettre à jour le statut de la commande
            commande.statut = 'validée'
            commande.save()

            # Créer une transaction liée à la commande
            Transaction.objects.create(
                acheteur=utilisateur,
                vendeur=None,
                commande=commande,
                montant=float(commande.montant_total),
                statut='validee'
            )

            #Envoyer un email de confirmation
            send_mail(
                subject='Confirmation de votre paiement',
                message=f"Bonjour {utilisateur.nom},\n\nVotre paiement de {commande.montant_total} € a bien été effectué. Merci pour votre achat sur MetaSouk !\n\nCordialement,\nL’équipe MetaSouk",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[utilisateur.email],
                fail_silently=False
            )

        messages.success(request, "Paiement effectué avec succès.")
        return redirect('client')

    # On transmet les données pour les pré-remplir dans le formulaire
    contexte = {
        'commande': commande,
        'nom_utilisateur': utilisateur.nom,
        'email_utilisateur': utilisateur.email,
    }
    return render(request, 'metasouk/paiement.html', contexte)
