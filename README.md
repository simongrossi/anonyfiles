# 🛡️ anonyfiles

**Anonyfiles** est une application Python open source permettant d'**anonymiser automatiquement des fichiers Word (.docx) et Excel (.xlsx)** en local. Elle détecte les données personnelles (noms, prénoms, dates, adresses, etc.) à l'aide de l'IA open source **spaCy**, puis les remplace ou les masque selon vos besoins.

---

## 🎯 Objectif

Fournir un outil **multiplateforme, 100 % local et RGPD-compliant**, pour anonymiser efficacement les documents contenant des données sensibles.

---

## ⚙️ Fonctionnalités

- ✅ Détection automatique des entités personnelles (noms, lieux, dates…)
- 🧠 Utilisation de **spaCy** en local (pas d'envoi de données)
- 📄 Support des formats **Word (.docx)** et **Excel (.xlsx)**
- 🔁 Remplacement configurable (balises ou données fictives via `Faker`)
- 💾 Génération d’un nouveau fichier anonymisé

---

## 📦 Installation

### 1. Cloner le dépôt

```bash
git clone https://github.com/votre-utilisateur/anonyfiles.git
cd anonyfiles
