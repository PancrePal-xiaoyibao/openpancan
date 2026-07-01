# OpenPanCan – 胰腺癌基因组分析系统

> **通过开源基因组分析赋能精准肿瘤学**

[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/fastapi-0.115-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-brightgreen.svg)](LICENSE)

**[English](README.md)** | **[中文](README_zh.md)** | **[日本語](docs/gene-base/README_ja.md)** | **[한국어](docs/gene-base/README_ko.md)** | **[Français](docs/gene-base/README_fr.md)**

---

OpenPanCan 是一个开源的、基于微服务的胰腺导管腺癌（PDAC）基因组分析平台，专为癌症研究和临床决策支持而构建。它通过 6 步流水线处理体细胞和胚系变异数据——从表型提取到临床报告生成——并提供全栈 Web 应用程序用于癌症患者管理。

**OpenPanCan 受 [OpenRare](https://github.com/OpenRare2026/OpenRare)（开源罕见病基因组分析系统）的架构启发并在此基础上构建。我们衷心感谢 OpenRare 团队在开源临床基因组学领域的开创性工作。**

---

## 🔬 核心功能

- **6 步癌症基因组流水线**：从 VCF 到临床报告的自动处理
- **癌症特异性变异注释**：VEP 结合 COSMIC、TCGA、OncoKB 丰富化
- **癌症驱动突变排序**：体细胞（VAF、热点、COSMIC）+ 胚系（ACMG）评分
- **胰腺癌信号通路研究原则**：纳入上游 RTK/ERBB-MET-FGFR 激活、下游 MAPK/PI3K-AKT-mTOR 级联再激活，以及 MYC 扩增、侵袭/转移等横向逃逸通路
- **靶向治疗推荐**：PARP 抑制剂、KRAS 抑制剂、免疫治疗匹配
- **临床试验匹配**：胰腺癌特异性试验搜索
- **全栈 Web 应用**：React + TypeScript 前端，支持中英双语

---

## 🏗 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    网关 (端口 8000)                           │
│                 FastAPI HTTP 代理                            │
└─────┬───────┬───────┬───────┬───────┬───────┬───────┐───────┘
      │       │       │       │       │       │       │
   8001    8002    8003    8004    8005    8006    8007
   ┌─┴─┐   ┌─┴─┐   ┌─┴─┐   ┌─┴─┐   ┌─┴─┐   ┌─┴─┐   ┌─┴──────┐
   │VEP│   │RAG│   │表型│   │PPI│   │排序│   │报告│   │胰腺癌  │
   │注释│   │提取│   │评分│   │评分│   │   │   │   │系统    │
   └───┘   └───┘   └───┘   └───┘   └───┘   └───┘   │(WebApp)│
                                                      └────────┘
```

### 模块说明

| 模块 | 端口 | 描述 |
|------|------|------|
| **vep_service** | 8001 | VEP 注释 + COSMIC/TCGA 癌症丰富化 |
| **phenotype_rag** | 8002 | 基于 LLM 的癌症表型提取 |
| **phenotype_score** | 8003 | COSMIC Census + TCGA 频率的癌症基因评分 |
| **ppi_score** | 8004 | 胰腺癌通路 PPI 网络评分 |
| **variant_rank** | 8005 | 癌症驱动突变排序（体细胞 + 胚系） |
| **report** | 8006 | 胰腺癌基因组报告生成（SSE 流式） |
| **PanCancerSystem** | 8007 | 全栈 Web 应用（React + FastAPI） |

---

## 🧬 癌症特异性基因数据库

OpenPanCan 使用以下癌症特异性基因数据库（替代 OpenRare 的罕见病专有数据库）：

| 数据库 | 用途 | 罕见病 → 癌症替换 |
|--------|------|-------------------|
| **COSMIC** | 癌症基因普查、突变频率 | 替代 Orphanet/OMIM |
| **TCGA-PAAD** | 胰腺腺癌突变数据 | 替代 MONDO 罕见病子集 |
| **OncoKB** | 癌症基因致癌注释 | 替代 PanelApp 基因面板 |
| **癌症热点数据库** | 已知癌症驱动突变 | 新增癌症特异性 |
| **ClinVar** | 临床变异意义 | 保留（通用） |
| **STRING DB** | 蛋白互作网络 | 保留（通用） |
| **GTEx** | 组织特异性基因表达 | 保留（通用） |
| **Reactome** | 生物通路数据 | 保留（通用） |
| **HPO** | 人类表型本体 | 保留（通用） |

---

## 🚀 快速开始

### 环境要求

- **Python** >= 3.12
- **uv**（Python 包管理器）– `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **VEP**（可选，用于 VCF 注释）– Ensembl Variant Effect Predictor
- **Node.js** >= 20（前端开发）

### 安装

```bash
# 克隆仓库
git clone https://github.com/PancrePal-xiaoyibao/OpenPanCan.git
cd OpenPanCan

# 复制并编辑环境配置
cp .env.example .env

# 安装所有模块依赖
make install
```

### 运行

```bash
# 通过网关启动所有模块
make start

# 或单独运行模块
make vep         # VEP 服务 (端口 8001)
make rag         # 表型 RAG (端口 8002)
make phenotype   # 表型评分 (端口 8003)
make ppi         # PPI 评分 (端口 8004)
make rank        # 变异排序 (端口 8005)
make report-srv  # 报告服务 (端口 8006)
make system      # 胰腺癌系统 (端口 8007)
```

## 📚 文档

- **[数据库配置说明](docs/database/current-configuration.md)** — 当前 stub 数据状态 + 环境变量
- **[数据库接入指南](docs/database/integration-guide.md)** — 真实数据逐步接入教程
- **[测试方案](docs/testing/test-plan.md)** — 单元测试 + 集成测试策略
- **[基因库文档](docs/gene-base/)** — 胰腺癌基因数据库（5 种语言）
- **[开发日志](DEVLOG.md)** — 项目完成情况 + 后续路线图
- **[API 参考](http://localhost:8000/docs)** — 交互式 API 文档（网关运行时）
- **[架构设计](docs/design/)** — 系统架构文档

**OpenPanCan 基于 [OpenRare](https://github.com/OpenRare2026/OpenRare) 的架构构建**——这一开创性的开源罕见病基因组分析系统。微服务架构、基于 HTTP 的模块通信模式、异步任务队列设计以及流水线编排方法均源自 OpenRare 优秀的工程基础。我们深深感谢 OpenRare 团队的远见和开源贡献，正是这些启发并促成了本项目的诞生。

---

## 📖 术语表

| 术语 | 全称 | 通俗解释 |
|------|------|----------|
| **VCF** | Variant Call Format（变异识别格式） | 存储基因变异数据的标准文件格式——可以理解为患者基因组中发现的所有 DNA 变化的电子表格 |
| **VEP** | Variant Effect Predictor（变异效应预测器） | Ensembl 提供的注释工具，告诉你每个变异会产生什么影响——是否改变蛋白质、落在基因的什么位置、严重程度如何 |
| **HPO** | Human Phenotype Ontology（人类表型本体） | 一套标准化的临床症状和体征词汇表，用计算机可理解的方式描述患者临床表现 |
| **COSMIC** | Catalogue Of Somatic Mutations In Cancer（癌症体细胞突变目录） | 全球最大的人类癌症突变数据库——告诉我们哪些突变是已知的癌症驱动因子 |
| **TCGA** | The Cancer Genome Atlas（癌症基因组图谱） | 里程碑式的癌症基因组项目，对 33 种癌症类型的 2 万多例肿瘤进行了测序，其中包括胰腺腺癌（PAAD） |
| **OncoKB** | Oncology Knowledge Base（肿瘤学知识库） | MSKCC 的精准肿瘤学数据库，按临床可操作性将癌症突变分为 Level 1–4 |
| **PPI** | Protein–Protein Interaction（蛋白质相互作用） | 细胞内蛋白质之间如何连接和通信的网络地图——帮助识别癌症通路中的关键基因 |
| **GTEx** | Genotype-Tissue Expression（基因型-组织表达） | 记录不同人体组织中哪些基因被"打开"（表达）的数据库，包括胰腺组织 |
| **ACMG** | American College of Medical Genetics（美国医学遗传学学会） | 发布胚系（遗传性）变异分类的权威指南：致病、可能致病、意义不明、可能良性、良性 |
| **AMP/ASCO/CAP** | 分子病理学协会 / 美国临床肿瘤学会 / 美国病理学家学院 | 三方联合发布的体细胞（肿瘤获得性）变异四层分类标准（Tier I–IV） |
| **VAF** | Variant Allele Frequency（变异等位基因频率） | 某位点上携带突变的 DNA 读段比例——帮助区分真正的体细胞驱动突变和测序噪音 |
| **SNV / INDEL** | 单核苷酸变异 / 插入缺失 | 最常见的两种小尺度基因变化：单个字母改变（SNV）或一小段 DNA 的插入/删除（INDEL） |
| **PDAC** | Pancreatic Ductal Adenocarcinoma（胰腺导管腺癌） | 最常见也最致命的胰腺癌类型，约占所有胰腺癌的 90% |
| **SSE** | Server-Sent Events（服务器推送事件） | 一种从服务器向浏览器实时推送更新的 Web 技术——报告模块用它在生成过程中实时显示进度 |

一句话总结：OpenPanCan 接收患者的 **VCF** 变异文件，通过 **VEP** 注释，用 **COSMIC/TCGA/OncoKB** 癌症数据丰富化，结合 **HPO** 表型和 **PPI** 癌症通路进行评分，依据 **VAF** 和 **ACMG/AMP** 指南排序驱动突变，最终通过 **SSE** 流式生成针对 **PDAC** 的临床报告。

---

## 📄 许可证

MIT License – 详见 [LICENSE](LICENSE)
