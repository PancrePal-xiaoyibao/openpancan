# OpenPanCan Gene Base — Base de Données Génomique du Cancer du Pancréas

**Plateforme d'analyse IA pour la génomique du cancer du pancréas**

---

## Vue d'ensemble

OpenPanCan Gene Base est une base de données génomique open source complète, conçue pour alimenter les analyses pilotées par l'intelligence artificielle dans la recherche sur le cancer du pancréas. Elle agrège, structure et enrichit les données génétiques provenant de multiples sources faisant autorité, offrant une fondation unifiée pour les modèles d'apprentissage automatique, les outils d'aide à la décision clinique et les applications de recherche.

Le cancer du pancréas demeure l'une des tumeurs malignes les plus meurtrières, avec un taux de survie à cinq ans inférieur à 12 %. Comprendre le paysage génomique — les mutations, les voies de signalisation et les biomarqueurs qui pilotent la tumorigenèse et influencent la réponse aux traitements — est essentiel pour améliorer les résultats cliniques. OpenPanCan Gene Base vise à accélérer cette compréhension en rendant les données génétiques de haute qualité accessibles, interopérables et prêtes pour l'IA.

## Gènes clés du cancer du pancréas

La base de données se concentre sur les gènes les plus significatifs sur le plan clinique et biologique dans l'adénocarcinome canalaire pancréatique (PDAC) :

| Gène | Rôle dans le cancer du pancréas |
|------|--------------------------------|
| **KRAS** | Oncogène majeur. Mutations activatrices dans >90 % des PDAC. Principal moteur de la tumorigenèse pancréatique. |
| **TP53** | Gène suppresseur de tumeur. Inactivé dans ~75 % des PDAC. La perte entraîne une instabilité génomique et une prolifération incontrôlée. |
| **SMAD4** | Gène suppresseur de tumeur. Délété ou muté dans ~55 % des PDAC. La perte est corrélée à la dissémination métastatique et à un mauvais pronostic. |
| **CDKN2A** | Gène suppresseur de tumeur (p16). Inactivé dans >90 % des PDAC. Perturbe la régulation du cycle cellulaire. |
| **BRCA1** | Gène de réparation de l'ADN. Les mutations germinales augmentent le risque de PDAC. Biomarqueur prédictif pour les inhibiteurs de PARP. |
| **BRCA2** | Gène de réparation de l'ADN. Principal gène de prédisposition héréditaire au PDAC. Guide la chimiothérapie à base de platine et l'utilisation des inhibiteurs de PARP. |
| **PALB2** | Gène de la voie de l'anémie de Fanconi. Les mutations augmentent le risque de PDAC et prédisent la sensibilité aux inhibiteurs de PARP. |
| **ATM** | Gène de réponse aux dommages de l'ADN. Mutations dans ~5 % des PDAC familiaux. Cible thérapeutique potentielle. |
| **ARID1A** | Gène de remodelage de la chromatine (complexe SWI/SNF). Mutations dans ~8 % des PDAC. Cible thérapeutique émergente. |
| **RNF43** | Régulateur de la voie Wnt. Muté dans ~6 % des PDAC, particulièrement dans le sous-type pancréaticobiliaire. |
| **STK11** | Gène suppresseur de tumeur (LKB1). Mutations rares mais pertinentes, associées aux cancers dépendants de KRAS. |
| **TGFBR2** | Récepteur de signalisation TGF-β. Mutations dans ~5 % des PDAC avec instabilité des microsatellites. |
| **MAP2K4** | Kinase activée par le stress. Mutations récurrentes dans le PDAC. Impliquée dans la signalisation JNK. |
| **GNAS** | Molécule de signalisation des protéines G. Mutations caractéristiques des néoplasmes mucineux papillaires intracanalaires (IPMN). |
| **KDM6A** | Histone déméthylase. Mutations dans ~5 % des PDAC. Régulateur épigénétique avec des effets biaisés par le sexe. |
| **RBM10** | Protéine de liaison à l'ARN. Mutations récurrentes dans le PDAC. Impliquée dans la régulation de l'épissage alternatif. |
| **SF3B1** | Composant du spliceosome. Mutations détectées dans le PDAC, associées à des profils d'épissage aberrants. |

## Sources de données

| Source | Description |
|--------|-------------|
| **COSMIC** | La plus grande base de données mondiale de mutations somatiques dans le cancer. Fournit les fréquences mutationnelles, les prédictions d'impact fonctionnel et les données de résistance aux médicaments. |
| **TCGA-PAAD** | Caractérisation multi-omique de l'adénocarcinome pancréatique incluant séquençage d'exome, RNA-seq, méthylation et données cliniques de centaines de patients. |
| **OncoKB** | Base de connaissances des variants oncogéniques, maintenue par MSKCC. Inclut les thérapies approuvées par la FDA et les traitements en investigation. |
| **ClinVar** | Archive publique du NCBI pour les variants génétiques humains avec interprétations de signification clinique, y compris les variants de prédisposition au cancer. |
| **GTEx** | Données d'expression génique et d'eQTL dans les tissus humains normaux, fournissant un contexte d'expression de référence pour le tissu pancréatique. |

## Structure du dépôt

```
openpancan-gene-base/
├── README.md                    # Anglais (principal)
├── README_zh.md                 # Chinois
├── README_ja.md                 # Japonais
├── README_ko.md                 # Coréen
├── README_fr.md                 # Français (ce fichier)
├── .gitignore
│
├── docs/
│   ├── design/                  # Documents d'architecture et de conception
│   ├── spec/                    # Spécifications techniques
│   ├── tasks/                   # Décomposition des tâches et suivi d'avancement
│   └── dev/                     # Guides de développement
│
├── data/                        # Fichiers de données génétiques
├── scripts/                     # Scripts de traitement de données et ETL
└── models/                      # Définitions et configurations des modèles IA/ML
```

## Relation avec OpenRare

OpenPanCan Gene Base s'inspire largement d'**OpenRare**, une plateforme open source pour l'analyse génomique des maladies rares. Nous remercions la communauté OpenRare pour son travail pionnier en matière de bases de données génétiques structurées et maintenues par la communauté. Alors qu'OpenRare couvre le domaine des maladies rares au sens large, OpenPanCan Gene Base se spécialise exclusivement dans le cancer du pancréas, en adaptant les modèles de données et l'intégration de l'IA aux besoins spécifiques de la recherche sur le PDAC.

## Démarrage rapide

```bash
git clone https://github.com/PancrePal-xiaoyibao/openpancan-gene-base-AI-insight-platform-for-pancreatic-cancer-.git
cd openpancan-gene-base
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Contribuer

Nous accueillons les contributions de la communauté de recherche sur le cancer du pancréas, des bioinformaticiens, des ingénieurs logiciels et de toute personne engagée dans l'amélioration des résultats pour les patients. Voir [docs/dev/README.md](docs/dev/README.md) pour les directives de contribution.

## Licence

Licence MIT

---

*Ensemble, transformons le cancer du pancréas d'une condamnation en une maladie chronique gérable.*
