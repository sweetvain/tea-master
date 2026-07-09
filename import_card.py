import json
import os
from app import app, db
from models import Card
from sqlalchemy import func

def import_and_analyze():
    json_path = 'collection.json'
    
    # 1. Vérification et lecture du fichier JSON
    if not os.path.exists(json_path):
        print(f"❌ Erreur : Le fichier '{json_path}' est introuvable à la racine.")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        try:
            cards_data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"❌ Erreur de lecture du JSON : {e}")
            return

    print(f"📦 {len(cards_data)} cartes trouvées dans le fichier JSON.")

    # 2. Utilisation du contexte Flask pour interagir avec instance/teacards.db
    with app.app_context():
        # Sécurité : On s'assure que la table existe
        db.create_all()

        added_count = 0
        skipped_count = 0

        print("⏳ Importation en cours dans la base SQLite...")
        for c in cards_data:
            # On vérifie si l'ID existe déjà pour éviter les crashs de clé primaire
            existing_card = Card.query.get(c.get('id'))
            
            if not existing_card:
                new_card = Card(
                    id=c.get('id'),
                    name=c.get('name'),
                    role=c.get('role'),
                    description=c.get('description'),
                    rarity=c.get('rarity'),
                    initials=c.get('initials'),
                    power=str(c.get('power')),  # Converti en string pour correspondre au modèle
                    photo=c.get('photo')
                )
                db.session.add(new_card)
                added_count += 1
            else:
                skipped_count += 1

        # Validation des changements
        if added_count > 0:
            db.session.commit()
        
        print(f"✅ Fin de l'import : {added_count} cartes ajoutées, {skipped_count} déjà existantes.")
        print("-" * 50)

        # 3. ANALYSE ET VÉRIFICATION DE LA LISTE
        print("📊 ANALYSE DE LA BASE DE DONNÉES (Table 'Card')")
        print("-" * 50)
        
        total_in_db = Card.query.count()
        print(f"• Nombre total de cartes actuellement en base : {total_in_db}")

        # Récupération de la répartition par rareté
        stats = db.session.query(Card.rarity, func.count(Card.id)).group_by(Card.rarity).all()
        
        print("\n• Répartition par rareté :")
        if stats:
            for rarity, count in stats:
                print(f"  - {rarity or 'Sans Rareté'} : {count} cartes")
        else:
            print("  - Aucune statistique disponible.")

        # Petit aperçu des 3 dernières cartes insérées pour vérification visuelle
        print("\n• Aperçu des 3 dernières cartes de la base :")
        last_cards = Card.query.limit(3).all()
        for card in last_cards:
            print(f"  [{card.rarity}] {card.name} - Rôle : {card.role or 'Aucun'}")

if __name__ == '__main__':
    import_and_analyze()