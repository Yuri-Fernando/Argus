"""Coloca `src/` no import path para os testes do serviço rodarem sem
instalação (`pip install -e`). Em produção o serviço é empacotado como
`inference_service` a partir de `src/`.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))
