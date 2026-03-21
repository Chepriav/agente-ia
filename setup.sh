#!/bin/bash
echo "Instalando hooks..."
cp hooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
echo "✅ Hooks instalados"
