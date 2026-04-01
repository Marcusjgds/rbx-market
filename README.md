# 🎮 RBX Market — Déploiement sur Render (GRATUIT)

## ✅ Fonctionnalités
- Connexion Roblox (cookie .ROBLOSECURITY)
- Solde Robux affiché en temps réel
- Upload modèles .rbxm / .rbxmx
- Prix libre (Gratuit ou Payant en Robux)
- Logo personnalisé
- Base de données SQLite persistante (tes fichiers ne disparaissent pas)
- Hébergement 24h/24 gratuit sur Render

---

## 🚀 Déploiement en ligne — Render.com

### Étape 1 — Mettre le code sur GitHub
1. Crée un compte sur **github.com** (gratuit)
2. Clique sur **"New repository"** → nomme-le `rbx-market`
3. Dézippe ce dossier sur ton PC
4. Upload tous les fichiers dans le repo GitHub (glisse-dépose)

### Étape 2 — Créer un compte Render
1. Va sur **render.com**
2. Clique **"Get Started for Free"**
3. Connecte-toi avec ton compte **GitHub**

### Étape 3 — Créer le service web
1. Dashboard Render → **"New +"** → **"Web Service"**
2. Connecte ton repo GitHub `rbx-market`
3. Render détecte automatiquement Python ✅
4. Paramètres :
   - **Name** : rbx-market
   - **Build Command** : `pip install -r requirements.txt`
   - **Start Command** : `gunicorn app:app --bind 0.0.0.0:$PORT`
   - **Plan** : Free ✅

### Étape 4 — Ajouter le disque persistant (pour garder les fichiers)
1. Dans ton service → onglet **"Disks"**
2. **"Add Disk"** :
   - Name : `rbx-market-data`
   - Mount Path : `/data`
   - Size : 1 GB (gratuit)
3. Ajoute la variable d'environnement :
   - **Key** : `PERSISTENT_DIR`
   - **Value** : `/data`

### Étape 5 — Déployer !
Clique **"Create Web Service"** → attends 2-3 minutes → ton site est en ligne !

🎉 Tu obtiens une URL du type : `https://rbx-market.onrender.com`

---

## ⚠️ Limite du plan gratuit Render
- Le site "dort" après 15 min sans visite (redémarre en ~30 sec au prochain accès)
- Pour éviter ça, utilise **UptimeRobot** (gratuit) pour pinger le site toutes les 10 min

---

## 🔑 Connexion Roblox
1. Va sur **roblox.com** → connecte-toi
2. **F12** → Application → Cookies → `roblox.com`
3. Copie la valeur de **`.ROBLOSECURITY`**
4. Colle-la dans le champ de connexion du site

---

## 💻 Test en local (optionnel)
```bash
pip install flask requests werkzeug gunicorn
python app.py
# Ouvre http://localhost:5000
```
