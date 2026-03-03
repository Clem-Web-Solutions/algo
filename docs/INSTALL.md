# Installation sur machine vierge — Debian 13 (utilisateur `debian`)

> Temps estimé : 10-15 minutes  
> Prérequis : accès SSH, connexion internet

---

## 1. Mise à jour du système

```bash
sudo apt update && sudo apt upgrade -y
```

---

## 2. Installer les dépendances système

```bash
sudo apt install -y \
    python3 \
    python3-venv \
    python3-pip \
    git \
    curl \
    ca-certificates
```

Vérifier la version Python (3.11+ recommandé, 3.9 minimum) :

```bash
python3 --version
```

---

## 3. Cloner le dépôt

```bash
cd /home/debian
git clone https://github.com/Clem-Web-Solutions/algo.git
cd algo
```

---

## 4. Créer l'environnement virtuel et installer les dépendances Python

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Vérifier que tout est installé :

```bash
python3 -c "import yfinance, pandas, numpy, sklearn, joblib, schedule, psutil; print('OK')"
```

---

## 5. Créer les dossiers de travail

```bash
mkdir -p data models reports logs
```

---

## 6. Test rapide du pipeline (un seul cycle)

```bash
python3 scripts/continuous_trainer.py --force-now
```

Ce test doit se terminer sans erreur et afficher les résultats de backtest pour AAPL, GOOGL, MSFT et TSLA.

---

## 7. Installer et démarrer le service systemd

```bash
# Copier le fichier de service
sudo cp scripts/algo-trainer.service /etc/systemd/system/

# Recharger systemd et activer le service au démarrage
sudo systemctl daemon-reload
sudo systemctl enable algo-trainer

# Corriger les permissions (important si le test étape 6 a tourné en root)
sudo chown -R debian:debian /home/debian/algo/data \
    /home/debian/algo/models \
    /home/debian/algo/reports \
    /home/debian/algo/logs 2>/dev/null || true

# Démarrer le service
sudo systemctl start algo-trainer

# Vérifier qu'il tourne
sudo systemctl status algo-trainer
```

Le service doit afficher `Active: active (running)`.

---

## 8. Surveiller les logs en temps réel

```bash
sudo journalctl -u algo-trainer -f
```

Vous devez voir dans les premières lignes :

```
Scheduler actif. Cycle toutes les 1 minute(s)
```

---

## Commandes utiles au quotidien

```bash
# État du service
sudo systemctl status algo-trainer

# Logs en direct
sudo journalctl -u algo-trainer -f

# Arrêter le service
sudo systemctl stop algo-trainer

# Redémarrer le service
sudo systemctl restart algo-trainer

# Forcer un cycle immédiatement (sans attendre le schedule)
cd /home/debian/algo
venv/bin/python3 scripts/continuous_trainer.py --force-now

# Voir l'état du walk-forward et les paramètres adaptés
cat data/trainer_state.json | python3 -m json.tool

# Voir le leaderboard de performance
cat data/performance_history.json | python3 -m json.tool

# Voir les logs du trainer (fichier)
ls reports/trainer_*.log
tail -100 reports/trainer_$(date +%Y%m).log
```

---

## Mise à jour du code depuis GitHub

```bash
cd /home/debian/algo
git pull
sudo systemctl restart algo-trainer
```

En cas de conflit local :

```bash
git stash && git pull && git stash pop
sudo systemctl restart algo-trainer
```

---

## Structure des fichiers générés

```
algo/
├── data/
│   ├── trainer_state.json       # État du walk-forward + surcharges adaptatives par ticker
│   ├── performance_history.json # Historique complet de chaque cycle
│   └── *.csv                    # Cache des données OHLCV téléchargées depuis yfinance
├── models/
│   └── model_AAPL.pkl           # Modèles entraînés sérialisés (un par ticker)
│   └── model_GOOGL.pkl
│   └── model_MSFT.pkl
│   └── model_TSLA.pkl
└── reports/
    ├── trainer_YYYYMM.log       # Log mensuel du continuous trainer
    └── production_report_*.txt  # Rapport détaillé par ticker et par cycle
```

---

## Dépannage

### Le service crash au démarrage
```bash
sudo journalctl -u algo-trainer -n 50 --no-pager
```
Cause fréquente : fichiers dans `data/` ou `models/` appartenant à `root` après un test sudo.  
Solution : `sudo chown -R debian:debian /home/debian/algo`

### `ModuleNotFoundError`
Le venv n'est pas activé ou `requirements.txt` n'a pas été installé dans le bon venv :
```bash
/home/debian/algo/venv/bin/pip install -r /home/debian/algo/requirements.txt
```

### `yfinance` ne télécharge pas de données
Vérifier la connexion réseau et les éventuels rate-limits :
```bash
/home/debian/algo/venv/bin/python3 -c "import yfinance as yf; print(yf.download('AAPL', period='5d'))"
```

### Changer les tickers surveillés
Éditer `src/core/config.py`, ligne `DEFAULT_TICKERS` :
```python
DEFAULT_TICKERS = ['AAPL', 'GOOGL', 'MSFT', 'TSLA']
```
Puis redémarrer le service.
