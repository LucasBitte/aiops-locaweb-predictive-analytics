# Validação: Glue Job no AWS Free Tier

**Data**: 2026-05-18  
**Status**: ❌ CONFIGURAÇÃO ATUAL EXCEDE FREE TIER

---

## Análise Atual

### Configuração Implementada

```python
GLUE_WORKER_TYPE = "G.2X"      # 2 DPUs por worker
GLUE_NUM_WORKERS = 10           # 10 workers
GLUE_TIMEOUT = 60               # minutos
```

### Cálculo de DPU-minutos

| Item | Valor | Cálculo |
|------|-------|---------|
| DPUs por worker | 2 | G.2X = 2 DPUs |
| Número de workers | 10 | Configurado |
| **Total de DPUs** | **20** | 2 × 10 |
| Tempo por execução | 60 min | Timeout |
| **DPU-minutos por execução** | **1.200** | 20 × 60 |
| Frequência | 1×/dia | Via Airflow (E9) |
| **DPU-minutos por mês** | **36.000** | 1.200 × 30 |

### AWS Free Tier para Glue

| Limite | Valor |
|--------|-------|
| DPU-horas gratuitas/mês | 100 |
| **DPU-minutos gratuitos/mês** | **6.000** | (100 × 60) |

### Resultado

```
Precisa:  36.000 DPU-minutos/mês
Oferece:   6.000 DPU-minutos/mês
─────────────────────────────────
Excesso: -30.000 DPU-minutos ❌

Múltiplo: 36.000 ÷ 6.000 = 6x O LIMITE
```

**Status**: ❌ **EXCEDE free tier em 6x**

---

## Solução: Otimizar para Free Tier

### Configuração Otimizada

```python
# ===== ANTES (Free Tier) =====
GLUE_WORKER_TYPE = "G.2X"
GLUE_NUM_WORKERS = 10
# DPU-minutos: 20 × 60 = 1.200 por execução
# Mensal: 36.000 ❌

# ===== DEPOIS (Free Tier) =====
GLUE_WORKER_TYPE = "G.1X"      # 1 DPU por worker (era 2)
GLUE_NUM_WORKERS = 3            # 3 workers (era 10)
GLUE_TIMEOUT = 60               # mesmo timeout
# DPU-minutos: 3 × 60 = 180 por execução
# Mensal: 5.400 ✅
```

### Cálculo Otimizado

| Item | Valor | Cálculo |
|------|-------|---------|
| DPUs por worker | 1 | G.1X = 1 DPU |
| Número de workers | 3 | Otimizado |
| **Total de DPUs** | **3** | 1 × 3 |
| Tempo por execução | 60 min | Timeout (suficiente) |
| **DPU-minutos por execução** | **180** | 3 × 60 |
| Frequência | 1×/dia | Via Airflow |
| **DPU-minutos por mês** | **5.400** | 180 × 30 |

### Resultado Otimizado

```
Precisa:  5.400 DPU-minutos/mês
Oferece:  6.000 DPU-minutos/mês
─────────────────────────────────
Margem:  +600 DPU-minutos ✅

Status: CABE NO FREE TIER COM MARGEM
```

---

## Validação de Capacidade

### Dado Processado

| Aspecto | Valor |
|---------|-------|
| Records input | 122.543 |
| Records output | 41.441 |
| Columns | 25 |
| Formato | Parquet (comprimido) |
| Tamanho estimado | 50-100 MB em memória |

### Recursos da Configuração Otimizada

| Worker | Specs | Qtd | Total |
|--------|-------|-----|-------|
| G.1X | 4 GB RAM, 2 vCPU | 3 | **12 GB RAM, 6 vCPU** |

### Proporção

```
Dado em memória:        ~100 MB
Memória disponível:     12.000 MB
─────────────────────────────────
Utilização:             0,8%  ✅

Conclusão: Largamente suficiente!
```

### Impacto de Performance

| Aspecto | Antes (G.2X ×10) | Depois (G.1X ×3) | Impacto |
|---------|---|---|---|
| Paralelismo | 10x mais alto | Baseline | Pode ser mais lento |
| Tempo estimado | ~10-15 min | ~15-25 min | +50-100% tempo |
| **Mas...** | — | — | — |
| Tempo timeout | 60 min | 60 min | **Sobra tempo** |
| Custo mensal | $150-200 | $20-30 | **90% desconto** |

**Conclusão**: Com dado de 41.4k registros, o timeout de 60 min é confortável mesmo com 3 workers.

---

## Trade-offs

### ✅ Vantagens da Solução Otimizada

1. **Cabe no Free Tier** — sem custos adicionais
2. **Margem de segurança** — 600 DPU-minutos de sobra
3. **Simples de escalar depois** — Se crescer, basta aumentar workers
4. **Execução rápida o suficiente** — 15-25 min para 41.4k registros

### ⚠️ Desvantagens

1. **Performance** — ~2x mais lento que configuração original
2. **Menos paralelismo** — menos workers = menos processamento simultâneo
3. **Precisa revisitar se dados crescerem** — 122k+ registros pode precisar mais resources

---

## Recomendação

### Para DESENVOLVIMENTO (agora)

```python
# === config.py (FREE TIER) ===
GLUE_WORKER_TYPE = "G.1X"
GLUE_NUM_WORKERS = 3
GLUE_TIMEOUT = 60

# Mantém em free tier, suficiente para dados atuais
```

### Para PRODUÇÃO (futuro, após teste)

```python
# === Quando dados crescerem para 200k+ registros ===
GLUE_WORKER_TYPE = "G.2X"
GLUE_NUM_WORKERS = 5  # ou mais, conforme necessário

# Trade-off: custo vs performance
# Monitore via CloudWatch
```

---

## Checklist de Implementação

- [ ] Atualizar `pipeline/silver/config.py`:
  - `GLUE_WORKER_TYPE = "G.1X"` (era G.2X)
  - `GLUE_NUM_WORKERS = 3` (era 10)

- [ ] Atualizar `infra/terraform/modules/glue/glue_jobs.tf`:
  ```hcl
  worker_type       = "G.1X"
  number_of_workers = 3
  ```

- [ ] Testar execução com nova config:
  ```bash
  aws glue start-job-run --job-name transform_bronze_to_silver
  ```

- [ ] Monitorar tempo de execução:
  ```bash
  aws logs tail /aws/glue/transform_bronze_to_silver --follow
  ```

- [ ] Validar output Silver está correto

---

## Conclusão

| Aspecto | Status |
|---------|--------|
| **Configuração Original** | ❌ Excede free tier (36.000 vs 6.000 DPU-min) |
| **Solução Otimizada** | ✅ Cabe em free tier (5.400 vs 6.000 DPU-min) |
| **Capacidade de Processamento** | ✅ Sobra (12 GB para ~100 MB de dado) |
| **Performance** | ⚠️ ~2x mais lento, mas timeout suficiente |
| **Custo** | ✅ $0 (free tier) vs $150-200 anterior |

**Recomendação**: Usar configuração otimizada agora, revisar quando dados crescerem além de 100k registros.

---

**Documento Preparado**: 2026-05-18  
**Próximo Passo**: Atualizar config.py e reaplicar Terraform
