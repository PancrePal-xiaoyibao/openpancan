# OpenPanCan Gene Base 胰腺癌基因数据库

**面向胰腺癌基因组学的人工智能洞察平台**

---

## 项目概述

OpenPanCan Gene Base 是一个开源的胰腺癌基因数据库，旨在为人工智能驱动的基因组分析提供数据基础。该项目汇聚整理了来自多个权威数据源的基因级别数据，为机器学习模型、临床决策支持工具以及科研应用提供统一的数据支撑。

胰腺癌是最致命的恶性肿瘤之一，五年生存率不足 12%。深入理解胰腺癌的基因组图谱——包括驱动肿瘤发生和影响治疗应答的突变、信号通路与生物标志物——对于改善患者预后至关重要。OpenPanCan Gene Base 通过构建高质量、可互操作且适配人工智能的基因数据平台，致力于加速这一理解进程。

## 关键胰腺癌基因

本数据库聚焦胰腺导管腺癌（PDAC）中具有重要临床与生物学意义的基因：

| 基因 | 在胰腺癌中的作用 |
|------|-----------------|
| **KRAS** | 核心癌基因，超过 90% 的 PDAC 病例存在激活突变，是胰腺癌发生的主要驱动因子。 |
| **TP53** | 抑癌基因，约 75% 的 PDAC 中存在失活。丧失后导致基因组不稳定性与不受控制的增殖。 |
| **SMAD4** | 抑癌基因，约 55% 的 PDAC 存在缺失或突变。缺失与转移扩散及不良预后相关。 |
| **CDKN2A** | 抑癌基因（p16），超过 90% 的 PDAC 中失活，导致细胞周期调控失调。 |
| **BRCA1** | DNA 损伤修复基因，种系突变增加 PDAC 发病风险，是 PARP 抑制剂治疗的预测性生物标志物。 |
| **BRCA2** | DNA 损伤修复基因，最常见的遗传性 PDAC 易感基因，指导含铂化疗和 PARP 抑制剂的使用。 |
| **PALB2** | Fanconi 贫血通路 DNA 修复基因，突变增加 PDAC 风险并预测 PARP 抑制剂敏感性。 |
| **ATM** | DNA 损伤应答基因，约 5% 的家族性 PDAC 存在突变，潜在治疗靶点。 |
| **ARID1A** | 染色质重塑基因（SWI/SNF 复合体），约 8% 的 PDAC 中突变，新兴治疗靶点。 |
| **RNF43** | Wnt 信号通路调控因子，约 6% 的 PDAC 中突变，尤其在胰胆管亚型中。 |
| **STK11** | 抑癌基因（LKB1），突变罕见但具有重要临床意义，与 KRAS 驱动型癌症相关。 |
| **TGFBR2** | TGF-β 信号受体，约 5% 微卫星不稳定 PDAC 中存在突变。 |
| **MAP2K4** | 应激激活激酶，PDAC 中反复突变，参与 JNK 信号通路。 |
| **GNAS** | G 蛋白信号分子，突变是导管内乳头状黏液性肿瘤（IPMN）的特征性变化。 |
| **KDM6A** | 组蛋白去甲基化酶，约 5% 的 PDAC 中突变，具有性别偏向性效应的表观遗传调控因子。 |
| **RBM10** | RNA 结合蛋白，PDAC 中反复突变，参与选择性剪接调控。 |
| **SF3B1** | 剪接体组分，PDAC 中检测到突变，与异常剪接模式相关。 |

## 数据来源

| 来源 | 说明 |
|------|------|
| **COSMIC**（癌症体细胞突变目录） | 全球最大、最全面的癌症体细胞突变数据库，提供突变频率、功能影响预测和耐药性数据。 |
| **TCGA-PAAD**（癌症基因组图谱—胰腺腺癌） | 包含数百例患者的外显子组测序、RNA-seq、甲基化和临床数据的多组学表征。 |
| **OncoKB**（精准肿瘤学知识库） | MSKCC 维护的致癌变异知识库，涵盖生物学与临床意义以及获批或在研的治疗方案。 |
| **ClinVar** | NCBI 的人类遗传变异公共档案，包含临床意义解读，包括种系癌症易感性变异。 |
| **GTEx**（基因型-组织表达） | 涵盖正常人体组织的基因表达和 eQTL 数据，为胰腺组织提供基线表达背景。 |

## 项目结构

```
openpancan-gene-base/
├── README.md                    # 英文主文档
├── README_zh.md                 # 中文文档（本文件）
├── README_ja.md                 # 日文文档
├── README_ko.md                 # 韩文文档
├── README_fr.md                 # 法文文档
├── .gitignore
│
├── docs/
│   ├── design/                  # 架构与设计文档
│   ├── spec/                    # 技术规范
│   ├── tasks/                   # 任务分解与进度追踪
│   └── dev/                     # 开发指南
│
├── data/                        # 基因数据文件
├── scripts/                     # 数据处理与 ETL 脚本
└── models/                      # AI/ML 模型定义与配置
```

## 与 OpenRare 的关系

OpenPanCan Gene Base 深受 **[OpenRare](https://github.com/rare-disease/openrare)** 项目的启发。OpenRare 是面向罕见疾病基因组分析的开源平台，率先探索了由社区维护的、面向特定疾病的结构化基因数据库模式。我们在此向 OpenRare 社区致以诚挚的感谢。

OpenRare 聚焦罕见疾病领域，而 OpenPanCan Gene Base 则专门针对胰腺癌，根据 PDAC 研究的独特需求来定制数据模型、基因注释和 AI 集成方案。

## 快速开始

```bash
git clone https://github.com/PancrePal-xiaoyibao/openpancan-gene-base-AI-insight-platform-for-pancreatic-cancer-.git
cd openpancan-gene-base
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 参与贡献

欢迎胰腺癌研究社区、生物信息学工作者、软件工程师以及所有关心胰腺癌患者的朋友贡献力量。详见 [docs/dev/README.md](docs/dev/README.md)。

## 许可证

MIT License

---

*让我们携手将胰腺癌从不治之症转变为可控的慢性病。*
