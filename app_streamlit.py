import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, text
import urllib.parse

# 1. Configuration de la page
st.set_page_config(page_title="Système MSDA", page_icon="🎓", layout="wide")

# 2. Gestion de la connexion UNIFIÉE
def get_engine():
    try:
        # Encodage du mot de passe pour gérer le '@'
        password = urllib.parse.quote_plus("Laay@222")
        url = f"mysql+mysqlconnector://root:{password}@127.0.0.1/classe"
        return create_engine(url)
    except Exception as e:
        st.error(f"Erreur critique de configuration : {e}")
        return None

def logger_action(action, details):
    engine = get_engine()
    if engine:
        try:
            with engine.begin() as conn:
                query = text("INSERT INTO historique_actions (utilisateur, action_type, details) VALUES (:u, :a, :d)")
                conn.execute(query, {"u": st.session_state["user"], "a": action, "d": details})
        except:
            pass 

# 3. Authentification sécurisée
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        st.title("🔐 Connexion au Système MSDA")
        user = st.text_input("Identifiant")
        pw = st.text_input("Mot de passe", type="password")
        
        if st.button("Se connecter", type="primary"):
            engine = get_engine()
            if engine:
                try:
                    with engine.connect() as conn:
                        query = text("SELECT * FROM utilisateurs WHERE identifiant=:u AND mot_de_passe=:p")
                        result = conn.execute(query, {"u": user, "p": pw}).fetchone()
                        
                        if result:
                            st.session_state["authenticated"] = True
                            st.session_state["user"] = user
                            st.rerun()
                        else:
                            st.error("Identifiant ou mot de passe incorrect")
                except Exception as e:
                    st.error(f"Impossible de contacter la base de données : {e}")
        return False
    return True

# --- EXECUTION ---
if check_password():
    # Navigation latérale
    st.sidebar.title(f"👤 {st.session_state['user']}")
    menu = st.sidebar.radio("Navigation", ["🔍 Consultation", "👥 Gestion Étudiants", "📝 Saisie des Notes", "📜 Historique"])
    
    if st.sidebar.button("Se déconnecter"):
        st.session_state["authenticated"] = False
        st.rerun()

    engine = get_engine()

    # --- PAGE 1 : CONSULTATION ---
    if menu == "🔍 Consultation":
        st.header("🔍 Consultation & Statistiques")
        matiere = st.text_input("Rechercher par matière", value="Python").strip()
        
        if st.button("Actualiser l'Affichage", type="primary"):
            try:
                query = text("SELECT e.nom, e.prenom, n.matiere, n.note, n.semestre "
                             "FROM etudiant e JOIN note n ON e.id_etudiant = n.id_etudiant "
                             "WHERE n.matiere = :m")
                df = pd.read_sql(query, engine, params={"m": matiere})
                
                if not df.empty:
                    df.columns = [c.capitalize() for c in df.columns]
                    col_m1, col_m2 = st.columns(2)
                    col_m1.metric("Moyenne Classe", f"{df['Note'].mean():.2f}/20")
                    col_m2.metric("Effectif", len(df))
                    
                    fig = px.histogram(df, x="Note", title=f"Répartition des notes en {matiere}", text_auto=True)
                    st.plotly_chart(fig, width='stretch')
                    
                    st.table(df)
                    
                    # Petit bouton d'export CSV (Requis par le projet !)
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button("📥 Télécharger les résultats (CSV)", csv, f"notes_{matiere}.csv", "text/csv")
                    
                    logger_action("CONSULTATION", f"A consulté {matiere}")
                else:
                    st.warning("Aucune note trouvée.")
            except Exception as e:
                st.error(f"Erreur SQL : {e}")

    # --- PAGE 2 : GESTION DES ÉTUDIANTS (CRUD) ---
    elif menu == "👥 Gestion Étudiants":
        st.header("👥 Gestion des Profils")
        t1, t2, t3 = st.tabs(["🆕 Ajouter", "✏️ Modifier", "🗑️ Supprimer"])

        # --- PAGE 2 : GESTION DES ÉTUDIANTS (AJOUT / MODIF / SUPPR) ---
        with t1:
            with st.form("add_student"):
                c1, c2 = st.columns(2)
                id_e = c1.number_input("ID", min_value=1, step=1)
                nom = c1.text_input("Nom")
                pre = c2.text_input("Prénom")
                sex = c2.selectbox("Sexe", ["M", "F"])
                dat = st.date_input("Naissance")
                
                if st.form_submit_button("Enregistrer"):
                    try:
                        with engine.begin() as conn:
                            conn.execute(text("INSERT INTO etudiant VALUES (:id, :n, :p, :s, :d)"),
                                       {"id": id_e, "n": nom, "p": pre, "s": sex, "d": dat})
                        st.success(f"✅ L'étudiant {nom} a été ajouté avec succès !")
                        logger_action("INSERTION", f"Étudiant {nom} (ID:{id_e})")
                    except Exception as e:
                        # Gestion spécifique de l'erreur de doublon (Clé Primaire)
                        if "Duplicate entry" in str(e):
                            st.error(f"⚠️ L'ID {id_e} existe déjà dans la base. Veuillez utiliser un autre identifiant.")
                        else:
                            st.error(f"❌ Erreur lors de l'enregistrement : {e}")

        with t2:
            st.subheader("Modifier un profil")
            id_mod = st.number_input("ID de l'étudiant à modifier", min_value=1, step=1, key="mod_stu")
            if st.button("Chercher"):
                df_st = pd.read_sql(text("SELECT * FROM etudiant WHERE id_etudiant=:id"), engine, params={"id":id_mod})
                if not df_st.empty: 
                    st.session_state['st_data'] = df_st.iloc[0]
                else:
                    st.warning("Aucun étudiant trouvé avec cet ID.")
            
            if 'st_data' in st.session_state:
                with st.form("edit_stu"):
                    new_n = st.text_input("Nom", value=st.session_state['st_data']['nom'])
                    new_p = st.text_input("Prénom", value=st.session_state['st_data']['prenom'])
                    if st.form_submit_button("Mettre à jour"):
                        with engine.begin() as conn:
                            conn.execute(text("UPDATE etudiant SET nom=:n, prenom=:p WHERE id_etudiant=:id"),
                                       {"n": new_n, "p": new_p, "id": id_mod})
                        st.success("Informations mises à jour !")
                        logger_action("MODIFICATION", f"Étudiant ID {id_mod}")
                        del st.session_state['st_data'] # Nettoyer après modification

        with t3:
            st.warning("⚠️ Action irréversible")
            id_del = st.number_input("ID à supprimer", min_value=1, step=1, key="del_stu")
            if st.button("Supprimer définitivement"):
                try:
                    with engine.begin() as conn:
                        # On supprime d'abord les notes à cause des clés étrangères
                        conn.execute(text("DELETE FROM note WHERE id_etudiant=:id"), {"id":id_del})
                        conn.execute(text("DELETE FROM etudiant WHERE id_etudiant=:id"), {"id":id_del})
                    st.success(f"L'étudiant ID {id_del} a été supprimé.")
                    logger_action("SUPPRESSION", f"Étudiant ID {id_del}")
                except Exception as e:
                    st.error(f"Erreur lors de la suppression : {e}")

    # --- PAGE 3 : SAISIE DES NOTES ---
    elif menu == "📝 Saisie des Notes":
        st.header("📝 Attribution des Notes")
        with st.form("note_form"):
            col_a, col_b = st.columns(2)
            id_n = col_a.number_input("ID Étudiant", min_value=1, step=1)
            mat_n = col_a.text_input("Matière")
            val_n = col_b.number_input("Note", min_value=0.0, max_value=20.0, step=0.5)
            sem_n = col_b.selectbox("Semestre", [1, 2])
            
            if st.form_submit_button("Valider la note"):
                try:
                    with engine.begin() as conn:
                        conn.execute(text("INSERT INTO note (id_etudiant, matiere, note, semestre) VALUES (:id, :m, :n, :s)"),
                                   {"id": id_n, "m": mat_n, "n": val_n, "s": sem_n})
                    st.success("Note enregistrée avec succès !")
                    logger_action("NOTE", f"Note {val_n} en {mat_n} pour ID {id_n}")
                except Exception as e:
                    # Ici l'erreur arrive souvent si l'étudiant n'existe pas dans la table 'etudiant'
                    st.error("Impossible d'ajouter la note. Vérifiez que l'ID étudiant existe bien dans la base.")
    # --- PAGE 4 : HISTORIQUE ---
    elif menu == "📜 Historique":
        st.header("📜 Historique des actions")
        df_h = pd.read_sql(text("SELECT * FROM historique_actions ORDER BY date_action DESC"), engine)
        st.dataframe(df_h, width='stretch')
        if st.button("Effacer les logs"):
            with engine.begin() as conn:
                conn.execute(text("DELETE FROM historique_actions"))
            st.rerun()