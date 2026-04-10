-- 1. Création de la base de données
CREATE DATABASE IF NOT EXISTS classe;
USE classe;

-- 2. Table des étudiants
CREATE TABLE IF NOT EXISTS etudiant (
    id_etudiant INT PRIMARY KEY,
    nom VARCHAR(50) NOT NULL,
    prenom VARCHAR(50) NOT NULL,
    sexe ENUM('M', 'F') NOT NULL,
    date_naissance DATE
) ENGINE=InnoDB;

-- 3. Table des notes (liée à l'étudiant)
CREATE TABLE IF NOT EXISTS note (
    id_note INT AUTO_INCREMENT PRIMARY KEY,
    id_etudiant INT,
    matiere VARCHAR(50) NOT NULL,
    note DECIMAL(4,2) CHECK (note BETWEEN 0 AND 20),
    semestre INT CHECK (semestre IN (1, 2)),
    FOREIGN KEY (id_etudiant) REFERENCES etudiant(id_etudiant) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 4. Table des utilisateurs (pour la connexion)
CREATE TABLE IF NOT EXISTS utilisateurs (
    id_user INT AUTO_INCREMENT PRIMARY KEY,
    identifiant VARCHAR(50) UNIQUE NOT NULL,
    mot_de_passe VARCHAR(100) NOT NULL
) ENGINE=InnoDB;

-- 5. Table d'historique (pour les logs)
CREATE TABLE IF NOT EXISTS historique_actions (
    id_action INT AUTO_INCREMENT PRIMARY KEY,
    utilisateur VARCHAR(50),
    action_type VARCHAR(50),
    details TEXT,
    date_action TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 6. Insertion d'un compte administrateur par défaut
-- Remplace 'admin' et '1234' par ce que tu veux pour tester
INSERT INTO utilisateurs (identifiant, mot_de_passe) 
VALUES ('admin', 'admin123')
ON DUPLICATE KEY UPDATE identifiant=identifiant;