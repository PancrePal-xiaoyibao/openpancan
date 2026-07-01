# OpenPanCan — 数据库接入开发任务清单

> **版本**: v0.1.0 → v0.2.0  
> **创建日期**: 2026-07-01  
> **负责人**: [待分配]  
> **预计总工时**: 10-14 天

---

## 📋 任务总览

| Phase | 数据库 | 模块 | 工时 | 优先级 | 状态 | 负责人 |
|-------|--------|------|------|--------|------|--------|
| 1 | COSMIC CGC | vep_service | 2d | P0 | ⏳ 待开始 | - |
| 2 | TCGA-PAAD | vep_service | 2d | P0 | ⏳ 待开始 | - |
| 3 | OncoKB API | variant_rank | 2d | P0 | ⏳ 待开始 | - |
| 4 | STRING DB | ppi_score | 3d | P1 | ⏳ 待开始 | - |
| 5 | GTEx | ppi_score | 2d | P1 | ⏳ 待开始 | - |
| 6 | HPO | phenotype_rag | 2d | P1 | ⏳ 待开始 | - |
| 7 | ClinicalTrials.gov | PanCancerSystem | 2d | P2 | ⏳ 待开始 | - |
| 8 | DGIdb | report | 2d | P2 | ⏳ 待开始 | - |
| 9 | 测试验证 | 全模块 | 2d | P0 | ⏳ 待开始 | - |

**状态**: ⏳ 待开始 | 🔄 进行中 | ✅ 已完成 | ❌ 阻塞

---

## Phase 1: COSMIC Cancer Gene Census 接入

### 基本信息

| 字段 | 值 |
|------|-----|
| **数据库** | COSMIC Cancer Gene Census |
| **来源** | https://cancer.sanger.ac.uk/cosmic/download |
| **文件** | `Cosmic_CancerGeneCensus_Tier1.tsv` |
| **许可证** | 学术免费（需注册） |
| **目标模块** | `modules/vep_service` |
| **工时估计** | 2 天 |

### 任务清单

| # | 任务 | 文件 | 状态 | 负责人 |
|---|------|------|------|--------|
| 1.1 | 注册 COSMIC 账号并下载 CGC TSV 文件 | - | ⏳ | - |
| 1.2 | 创建 `data_loaders/cosmic_cgc.py` 加载器 | `modules/vep_service/src/vep_service/data_loaders/cosmic_cgc.py` | ⏳ | - |
| 1.3 | 实现 `_load_cgc_from_file()` 函数 | 同上 | ⏳ | - |
| 1.4 | 实现 `get_cosmic_cgc()` 缓存函数 | 同上 | ⏳ | - |
| 1.5 | 删除 `cancer_annotation.py` 硬编码 `COSMIC_CANCER_GENE_CENSUS` | `modules/vep_service/src/vep_service/cancer_annotation.py` | ⏳ | - |
| 1.6 | 在 `add_cancer_annotations()` 中调用新加载器 | 同上 | ⏳ | - |
| 1.7 | 添加单元测试 `test_cosmic_cgc.py` | `tests/unit/test_cosmic_cgc.py` | ⏳ | - |
| 1.8 | 更新 `.env.example` 添加 `COSMIC_DATA_DIR` 路径说明 | `.env.example` | ⏳ | - |

### 验收标准

```python
# 测试用例
assert len(get_cosmic_cgc()) > 500  # CGC 有 ~700 基因
assert get_cosmic_cgc()["KRAS"]["role"] == "oncogene"
assert get_cosmic_cgc()["TP53"]["role"] == "TSG"
```

### 数据目录结构

```
reference_data/cosmic/
├── Cosmic_CancerGeneCensus_Tier1.tsv
└── README.md  # 数据来源说明
```

---

## Phase 2: TCGA-PAAD 突变频率接入

### 基本信息

| 字段 | 值 |
|------|-----|
| **数据库** | TCGA Pancreatic Adenocarcinoma (PAAD) |
| **来源** | https://portal.gdc.cancer.gov/projects/TCGA-PAAD |
| **文件** | Mutect2 Masked Somatic Mutation MAF |
| **许可证** | 开放 (dbGaP) |
| **目标模块** | `modules/vep_service`, `modules/phenotype_score` |
| **工时估计** | 2 天 |

### 任务清单

| # | 任务 | 文件 | 状态 | 负责人 |
|---|------|------|------|--------|
| 2.1 | 从 GDC Portal 下载 TCGA-PAAD MAF 文件 | - | ⏳ | - |
| 2.2 | 创建 `data_loaders/tcga_paad.py` | `modules/vep_service/src/vep_service/data_loaders/tcga_paad.py` | ⏳ | - |
| 2.3 | 实现 `_compute_tcga_paad_freq()` 频率计算 | 同上 | ⏳ | - |
| 2.4 | 实现 `get_tcga_paad_freq()` 缓存函数 | 同上 | ⏳ | - |
| 2.5 | 删除硬编码 `TCGA_PAAD_FREQUENCIES` dict | `cancer_annotation.py`, `cancer_scoring.py` | ⏳ | - |
| 2.6 | 在 `phenotype_score` 模块复用加载器 | `modules/phenotype_score/src/phenotype_score/cancer_scoring.py` | ⏳ | - |
| 2.7 | 添加单元测试 | `tests/unit/test_tcga_paad.py` | ⏳ | - |

### 验收标准

```python
# 测试用例
freq = get_tcga_paad_freq()
assert freq["KRAS"] > 0.90  # KRAS 在 PAAD 中 ~93%
assert freq["TP53"] > 0.70  # TP53 在 PAAD 中 ~75%
assert freq["SMAD4"] > 0.20  # SMAD4 ~22%
```

---

## Phase 3: OncoKB API 集成

### 基本信息

| 字段 | 值 |
|------|-----|
| **数据库** | OncoKB (MSKCC) |
| **来源** | https://www.oncokb.org/api |
| **API** | `https://www.oncokb.org/api/v1/annotate/mutations/byHGVS` |
| **许可证** | 学术免费（需 API Token） |
| **目标模块** | `modules/variant_rank`, `modules/vep_service` |
| **工时估计** | 2 天 |

### 任务清单

| # | 任务 | 文件 | 状态 | 负责人 |
|---|------|------|------|--------|
| 3.1 | 注册 OncoKB 账号获取 API Token | - | ⏳ | - |
| 3.2 | 创建 `services/oncokb_client.py` | `modules/variant_rank/src/variant_rank/services/oncokb_client.py` | ⏳ | - |
| 3.3 | 实现 `OncoKBClient` 类（异步 HTTP 客户端） | 同上 | ⏳ | - |
| 3.4 | 实现 `annotate_variant(hgvsg)` 方法 | 同上 | ⏳ | - |
| 3.5 | 实现 `oncokb_level_to_score()` 映射 | 同上 | ⏳ | - |
| 3.6 | 在 `somatic_scoring.py` 中集成 API 调用 | `modules/variant_rank/src/variant_rank/somatic_scoring.py` | ⏳ | - |
| 3.7 | 添加 `ONCOKB_API_KEY` 到 `.env.example` | `.env.example` | ⏳ | - |
| 3.8 | 添加 API 调用测试（Mock 响应） | `tests/unit/test_oncokb_client.py` | ⏳ | - |

### 验收标准

```python
# 测试用例
oncokb = OncoKBClient(api_key="test")
result = await oncokb.annotate_variant("7:g.140753336A>T")  # KRAS G12D
assert result.get("oncogenic") == "Oncogenic"
assert oncokb.oncokb_level_to_score("LEVEL_1") == 10.0
```

---

## Phase 4: STRING DB PPI 网络接入

### 基本信息

| 字段 | 值 |
|------|-----|
| **数据库** | STRING DB v12 |
| **来源** | https://string-db.org/download |
| **文件** | `9606.protein.links.detailed.v12.0.txt.gz` + `protein.info` |
| **许可证** | CC BY 4.0 |
| **目标模块** | `modules/ppi_score` |
| **工时估计** | 3 天 |

### 任务清单

| # | 任务 | 文件 | 状态 | 负责人 |
|---|------|------|------|--------|
| 4.1 | 下载 STRING DB 文件（links + info） | - | ⏳ | - |
| 4.2 | 创建 `data_loaders/string_db.py` | `modules/ppi_score/src/ppi_score/data_loaders/string_db.py` | ⏳ | - |
| 4.3 | 实现 `_parse_string_id()` protein ID 解析 | 同上 | ⏳ | - |
| 4.4 | 实现 `_load_string_network()` 网络加载 | 同上 | ⏳ | - |
| 4.5 | 实现 `get_string_network()` 缓存函数 | 同上 | ⏳ | - |
| 4.6 | 实现 ENSG → HGNC symbol 映射 | 同上 | ⏳ | - |
| 4.7 | 删除硬编码 `PANCREATIC_CANCER_PPI` dict | `modules/ppi_score/src/ppi_score/cancer_ppi.py` | ⏳ | - |
| 4.8 | 在 `CancerPPIScorer` 中集成 STRING 网络 | 同上 | ⏳ | - |
| 4.9 | 添加单元测试 | `tests/unit/test_string_db.py` | ⏳ | - |

### 验收标准

```python
# 测试用例
net = get_string_network()
assert len(net) > 1000000  # STRING 有数百万互作
assert ("KRAS", "TP53") in net or ("TP53", "KRAS") in net
assert net[("KRAS", "TP53")]["combined"] > 400
```

---

## Phase 5: GTEx 胰腺组织表达接入

### 基本信息

| 字段 | 值 |
|------|-----|
| **数据库** | GTEx v11 |
| **来源** | https://gtexportal.org/home/datasets |
| **文件** | `GTEx_Analysis_v11_RSEMv1.3.3_gene_median_tpm.gct.gz` |
| **许可证** | dbGaP（需申请） |
| **目标模块** | `modules/ppi_score`, `modules/phenotype_score` |
| **工时估计** | 2 天 |

### 任务清单

| # | 任务 | 文件 | 状态 | 负责人 |
|---|------|------|------|--------|
| 5.1 | 下载 GTEx v11 median TPM GCT 文件 | - | ⏳ | - |
| 5.2 | 创建 `data_loaders/gtex.py` | `modules/ppi_score/src/ppi_score/data_loaders/gtex.py` | ⏳ | - |
| 5.3 | 实现 `_load_gtex()` GCT 解析 | 同上 | ⏳ | - |
| 5.4 | 实现 `get_gtex_pancreas_tpm(gene)` 函数 | 同上 | ⏳ | - |
| 5.5 | 在 `CancerPPIScorer` 中使用胰腺 TPM 加权 | `cancer_ppi.py` | ⏳ | - |
| 5.6 | 在 `phenotype_score` 中使用组织表达信息 | `cancer_scoring.py` | ⏳ | - |
| 5.7 | 添加单元测试 | `tests/unit/test_gtex.py` | ⏳ | - |

### 验收标准

```python
# 测试用例
tpm = get_gtex_pancreas_tpm("KRAS")
assert tpm > 0  # KRAS 在胰腺有表达
# 检查胰腺高表达基因
assert get_gtex_pancreas_tpm("INS") > 100  # 胰岛素高表达
```

---

## Phase 6: HPO 本体解析接入

### 基本信息

| 字段 | 值 |
|------|-----|
| **数据库** | Human Phenotype Ontology |
| **来源** | https://hpo.jax.org/app/data/ontology |
| **文件** | `hp.obo` + `phenotype.hpoa` |
| **许可证** | 自定义（学术/临床免费） |
| **目标模块** | `modules/phenotype_rag` |
| **工时估计** | 2 天 |

### 任务清单

| # | 任务 | 文件 | 状态 | 负责人 |
|---|------|------|------|--------|
| 6.1 | 下载 `hp.obo` 和 `phenotype.hpoa` | - | ⏳ | - |
| 6.2 | 创建 `data_loaders/hpo.py` | `modules/phenotype_rag/src/phenotype_rag/data_loaders/hpo.py` | ⏳ | - |
| 6.3 | 实现 `_parse_obo()` OBO 格式解析 | 同上 | ⏳ | - |
| 6.4 | 实现 `get_hpo_term(hpo_id)` 查询 | 同上 | ⏳ | - |
| 6.5 | 实现 `get_hpo_by_name()` 名称模糊匹配 | 同上 | ⏳ | - |
| 6.6 | 删除硬编码 `PANCREATIC_CANCER_HPO_TERMS` dict | `modules/phenotype_rag/src/phenotype_rag/pipeline.py` | ⏳ | - |
| 6.7 | 在 `CancerPhenotypePipeline` 中使用新加载器 | 同上 | ⏳ | - |
| 6.8 | 添加单元测试 | `tests/unit/test_hpo.py` | ⏳ | - |

### 验收标准

```python
# 测试用例
hpo = get_hpo_term("HP:0004364")
assert hpo["name"] == "Pancreatic adenocarcinoma"
matches = get_hpo_by_name("pancreatic")
assert len(matches) > 5  # 多个胰腺相关 HPO
```

---

## Phase 7: ClinicalTrials.gov API 接入

### 基本信息

| 字段 | 值 |
|------|-----|
| **数据库** | ClinicalTrials.gov API v2 |
| **来源** | https://clinicaltrials.gov/api/v2/studies |
| **API** | 免费，无需 Token |
| **目标模块** | `modules/PanCancerSystem`, `modules/report` |
| **工时估计** | 2 天 |

### 任务清单

| # | 任务 | 文件 | 状态 | 负责人 |
|---|------|------|------|--------|
| 7.1 | 研究 API v2 文档 | - | ⏳ | - |
| 7.2 | 创建 `services/clinicaltrials_client.py` | `modules/PanCancerSystem/backend/services/clinicaltrials_client.py` | ⏳ | - |
| 7.3 | 实现 `search_pancreatic_cancer_trials()` | 同上 | ⏳ | - |
| 7.4 | 实现 `search_trials_by_gene(gene)` | 同上 | ⏳ | - |
| 7.5 | 删除硬编码 `_PANCREATIC_CANCER_TRIALS` list | `modules/PanCancerSystem/backend/api/trials.py` | ⏳ | - |
| 7.6 | 在 `api/trials.py` 中集成 API 调用 | 同上 | ⏳ | - |
| 7.7 | 在 `report` 模块复用服务 | `modules/report/src/report/report/clinical_trials.py` | ⏳ | - |
| 7.8 | 添加单元测试（Mock API 响应） | `tests/unit/test_clinicaltrials.py` | ⏳ | - |

### 验收标准

```python
# 测试用例
trials = await search_pancreatic_cancer_trials(gene="KRAS")
assert len(trials) > 0  # 应返回 KRAS 相关试验
assert "NCT" in trials[0]["protocolSection"]["identificationModule"]["nctId"]
```

---

## Phase 8: DGIdb 药物-基因数据库接入

### 基本信息

| 字段 | 值 |
|------|-----|
| **数据库** | DGIdb (Drug Gene Interaction Database) |
| **来源** | https://dgidb.org/api |
| **API** | 免费 |
| **目标模块** | `modules/report` |
| **工时估计** | 2 天 |

### 任务清单

| # | 任务 | 文件 | 状态 | 负责人 |
|---|------|------|------|--------|
| 8.1 | 研究 DGIdb API 文档 | - | ⏳ | - |
| 8.2 | 创建 `services/dgidb_client.py` | `modules/report/src/report/services/dgidb_client.py` | ⏳ | - |
| 8.3 | 实现 `get_drugs_for_gene(gene)` | 同上 | ⏳ | - |
| 8.4 | 实现 `get_drug_interactions(genes)` | 同上 | ⏳ | - |
| 8.5 | 删除硬编码 `DRUG_RECOMMENDATIONS` list | `modules/report/src/report/report/drug_recommendations.py` | ⏳ | - |
| 8.6 | 在 `get_drug_recommendations()` 中集成 API | 同上 | ⏳ | - |
| 8.7 | 添加单元测试 | `tests/unit/test_dgidb.py` | ⏳ | - |

### 验收标准

```python
# 测试用例
drugs = await get_drugs_for_gene("KRAS")
assert len(drugs) > 0
# 检查 PARP 抑制剂与 BRCA1 的关联
brca_drugs = await get_drugs_for_gene("BRCA1")
assert any("olaparib" in d["drug_name"].lower() for d in brca_drugs)
```

---

## Phase 9: 测试验证与文档更新

### 任务清单

| # | 任务 | 文件 | 状态 | 负责人 |
|---|------|------|------|--------|
| 9.1 | 运行全部单元测试 | `tests/unit/` | ⏳ | - |
| 9.2 | 运行集成测试（Gateway + 模块） | `tests/integration/` | ⏳ | - |
| 9.3 | 端到端流水线测试（sample.vcf） | `tests/integration/test_pipeline.py` | ⏳ | - |
| 9.4 | 更新 `docs/database/current-configuration.md` | 同上 | ⏳ | - |
| 9.5 | 更新 `DEVLOG.md` 完成状态 | `DEVLOG.md` | ⏳ | - |
| 9.6 | 更新 `CHANGELOG.md` v0.2.0 发布 | `CHANGELOG.md` | ⏳ | - |

---

## 📁 数据文件目录结构

所有数据文件放置在 `reference_data/` 目录：

```
reference_data/
├── README.md                     # 数据来源总说明
├── cosmic/
│   ├── Cosmic_CancerGeneCensus_Tier1.tsv
│   └── README.md
├── tcga/
│   ├── tcga_paad_mc3_public.tsv
│   └── README.md
├── gtex/
│   ├── GTEx_Analysis_v11_RSEMv1.3.3_gene_median_tpm.gct.gz
│   └── README.md
├── hpo/
│   ├── hp.obo
│   ├── phenotype.hpoa
│   └── README.md
├── string/
│   ├── 9606.protein.links.detailed.v12.0.txt.gz
│   ├── 9606.protein.info.v12.0.txt.gz
│   └── README.md
├── depmap/
│   ├── CRISPRGeneEffect.csv
│   └── README.md
├── hgnc/
│   ├── hgnc_complete_set.txt
│   └── README.md
└── clinvar/
    ├── variant_summary.txt.gz
    └── README.md
```

---

## 🔗 相关文档

- [当前配置说明](./current-configuration.md)
- [接入详细指南](./integration-guide.md)
- [测试方案](../testing/test-plan.md)
- [架构文档](../design/architecture.md)

---

## 📊 进度追踪

更新此文档中的状态列：

- ⏳ → 🔄（开始开发）
- 🔄 → ✅（完成任务）
- ❌（遇到阻塞，注明原因）

每次更新后提交到 Git：

```bash
git add docs/database/tasks.md
git commit -m "docs: update database integration progress"
git push origin main
```

---

## 🤝 协作指南

### 分工建议

| 开发者 | 负责 Phase |
|--------|------------|
| A | Phase 1-2（COSMIC + TCGA） |
| B | Phase 3-4（OncoKB + STRING） |
| C | Phase 5-6（GTEx + HPO） |
| D | Phase 7-8（ClinicalTrials + DGIdb） |
| E | Phase 9（测试 + 文档） |

### 每日同步

- 更新本文档状态
- 提交代码到独立分支：`feat/database-phase-{n}`
- 合并到 main 前需通过单元测试

### 阻塞处理

遇到阻塞时：
1. 在本文档标记 ❌
2. 添加阻塞原因注释
3. 在 GitHub Issues 创建问题
4. 通知其他开发者

---

*此文档用于协同开发，请及时更新进度状态。*