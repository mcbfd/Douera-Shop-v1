
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from urllib.parse import urlparse

def check_db():
    url = os.getenv('POSTGRES_URL')
    if not url:
        print("POSTGRES_URL non trouvée")
        return

    result = urlparse(url)
    try:
        conn = psycopg2.connect(
            database=result.path[1:],
            user=result.username,
            password=result.password,
            host=result.hostname,
            port=result.port
        )
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # 1. Lister les tables
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        tables = cur.fetchall()
        print(f"Tables trouvées: {[t['table_name'] for t in tables]}")
        
        # 2. Inspecter les avis
        if any(t['table_name'] == 'reviews' for t in tables):
            cur.execute("SELECT COUNT(*) as count FROM reviews")
            count = cur.fetchone()['count']
            print(f"Nombre d'avis dans la table: {count}")
            
            if count > 0:
                cur.execute("SELECT * FROM reviews LIMIT 5")
                rows = cur.fetchall()
                print("Derniers avis:")
                for r in rows:
                    print(r)
        else:
            print("LA TABLE 'reviews' N'EXISTE PAS !")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Erreur DB: {e}")

if __name__ == "__main__":
    check_db()
