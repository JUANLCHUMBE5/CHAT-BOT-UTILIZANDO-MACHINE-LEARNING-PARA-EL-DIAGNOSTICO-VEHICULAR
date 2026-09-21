"""
Benchmark V4 Oficial y Tabla de Ground Truth a Priori — CarBot (Fase 7)
Conjunto de prueba 100% ciego e inédito (sin solapamiento con V2 ni V3).
Estructurado en dos submódulos especializados (< 500 líneas c/u):
  - G1 (scripts.benchmark_v4_g1_casos): 50 casos técnicos con modelo vehicular y DTC.
  - G2 (scripts.benchmark_v4_g2_casos): 50 casos en lenguaje coloquial de taller.
"""

from typing import Any, Dict, List

from scripts.benchmark_v4_g1_casos import BENCHMARK_V4_G1_CASOS
from scripts.benchmark_v4_g2_casos import BENCHMARK_V4_G2_CASOS

# Consolidado oficial de 100 casos ciegos
BENCHMARK_V4_CASOS: List[Dict[str, Any]] = BENCHMARK_V4_G1_CASOS + BENCHMARK_V4_G2_CASOS
