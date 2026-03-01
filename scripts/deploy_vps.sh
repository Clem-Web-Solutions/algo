#!/bin/bash
# =============================================================================
# deploy_vps.sh - Script d'installation et demarrage du continuous trainer
# Executer UNE SEULE FOIS sur le VPS en tant que root ou avec sudo
#
# Usage:
#   chmod +x scripts/deploy_vps.sh
#   sudo bash scripts/deploy_vps.sh
# =============================================================================

set -e  # Arreter en cas d'erreur

ALGO_DIR="/home/debian/algo"
VENV_DIR="$ALGO_DIR/venv"
SERVICE_FILE="$ALGO_DIR/scripts/algo-trainer.service"
SERVICE_NAME="algo-trainer"

echo "=============================================="
echo " ALGO TRADING - DEPLOY VPS"
echo "=============================================="

# --- 1. Verifier que le projet existe ---
if [ ! -d "$ALGO_DIR" ]; then
    echo "[ERREUR] Dossier $ALGO_DIR non trouve"
    echo "  -> Cloner le projet d'abord: git clone <repo> $ALGO_DIR"
    exit 1
fi
echo "[OK] Dossier projet: $ALGO_DIR"

# --- 2. Verifier le venv ---
if [ ! -f "$VENV_DIR/bin/python3" ]; then
    echo "[INFO] Creation du venv..."
    cd "$ALGO_DIR"
    python3 -m venv venv
fi
echo "[OK] Venv: $VENV_DIR"

# --- 3. Installer les dependances ---
echo "[INFO] Installation des dependances Python..."
"$VENV_DIR/bin/pip" install --quiet --upgrade pip
"$VENV_DIR/bin/pip" install --quiet \
    yfinance pandas numpy scikit-learn joblib schedule psutil

echo "[OK] Dependances installees"

# --- 4. Creer les dossiers necessaires ---
for dir in "$ALGO_DIR/data" "$ALGO_DIR/models" "$ALGO_DIR/reports" "$ALGO_DIR/logs"; do
    mkdir -p "$dir"
done
echo "[OK] Dossiers crees"

# --- 5. Installer le service systemd ---
echo "[INFO] Installation du service systemd..."
cp "$SERVICE_FILE" /etc/systemd/system/
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
echo "[OK] Service installe et active au demarrage"

# --- 6. Test rapide (dry-run) ---
echo "[INFO] Test du pipeline (un cycle immediat)..."
cd "$ALGO_DIR"
"$VENV_DIR/bin/python3" scripts/continuous_trainer.py --force-now
echo "[OK] Test reussi"

# --- 6b. Corriger les permissions (le test tourne en root, le service en debian) ---
echo "[INFO] Correction des permissions..."
chown -R debian:debian "$ALGO_DIR/data" 2>/dev/null || true
chown -R debian:debian "$ALGO_DIR/models" 2>/dev/null || true
chown -R debian:debian "$ALGO_DIR/reports" 2>/dev/null || true
chmod -R u+rw "$ALGO_DIR/data" 2>/dev/null || true
echo "[OK] Permissions corrigees"

# --- 7. Demarrer le service ---
echo "[INFO] Demarrage du service..."
systemctl start "$SERVICE_NAME"
sleep 2
systemctl status "$SERVICE_NAME" --no-pager

echo ""
echo "=============================================="
echo " INSTALLATION TERMINEE"
echo "=============================================="
echo ""
echo "  Commandes utiles:"
echo "    sudo systemctl status $SERVICE_NAME     # Etat du service"
echo "    sudo journalctl -u $SERVICE_NAME -f     # Logs en temps reel"
echo "    sudo systemctl stop $SERVICE_NAME       # Arreter"
echo "    sudo systemctl restart $SERVICE_NAME    # Redemarrer"
echo ""
echo "  Forcer un cycle immediatement:"
echo "    cd $ALGO_DIR && venv/bin/python3 scripts/continuous_trainer.py --force-now"
echo ""
echo "  Voir le leaderboard:"
echo "    cat $ALGO_DIR/data/performance_history.json | python3 -m json.tool"
echo ""
echo "  Le prochain cycle automatique est a 22:00 UTC chaque soir."
echo "=============================================="
