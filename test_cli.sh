#!/bin/bash
set -e

echo "🧪 Création du fichier de test..."
mkdir -p tests mappings log
cat <<EOF > tests/sample.txt
Jean Dupont est né à Paris et travaille chez ACME Corp. Son email est jean.dupont@email.com
EOF

echo "🚀 Lancement de l’anonymisation..."
python anonyfiles_cli/main.py anonymize tests/sample.txt \
  --output tests/result.txt \
  --config anonyfiles_cli/config.yaml

echo ""
echo "📄 Résultat anonymisé :"
cat tests/result.txt

echo ""
echo "📁 Fichier de mapping généré :"
latest_mapping=$(ls -t mappings/sample_mapping_*.csv | head -n 1)
cat "$latest_mapping"

echo ""
echo "📊 Log des entités détectées :"
latest_log=$(ls -t log/sample_entities_*.csv | head -n 1)
cat "$latest_log"
