// =============================================================================
// OpenPanCan - Simple i18n (English / Chinese)
// =============================================================================

export type Language = 'en' | 'zh';

type TranslationMap = Record<string, string>;

const en: TranslationMap = {
  // Navigation
  'nav.dashboard': 'Dashboard',
  'nav.patients': 'Patients',
  'nav.variants': 'Variants',
  'nav.reports': 'Reports',
  'nav.pipeline': 'Pipeline',
  'nav.settings': 'Settings',
  'nav.gene': 'Gene',

  // Common
  'common.loading': 'Loading...',
  'common.error': 'Error',
  'common.save': 'Save',
  'common.cancel': 'Cancel',
  'common.delete': 'Delete',
  'common.edit': 'Edit',
  'common.create': 'Create',
  'common.search': 'Search',
  'common.filter': 'Filter',
  'common.export': 'Export',
  'common.download': 'Download',
  'common.refresh': 'Refresh',
  'common.back': 'Back',
  'common.next': 'Next',
  'common.previous': 'Previous',
  'common.confirm': 'Confirm',
  'common.no_data': 'No data available',
  'common.actions': 'Actions',
  'common.status': 'Status',
  'common.details': 'Details',
  'common.close': 'Close',
  'common.yes': 'Yes',
  'common.no': 'No',

  // Patients
  'patient.title': 'Cancer Patients',
  'patient.create': 'Add Patient',
  'patient.code': 'Patient Code',
  'patient.age': 'Age',
  'patient.gender': 'Gender',
  'patient.diagnosis': 'Diagnosis',
  'patient.cancer_type': 'Cancer Type',
  'patient.stage': 'Stage',
  'patient.tumor_site': 'Tumor Site',
  'patient.survival': 'Survival Status',
  'patient.created': 'Created',
  'patient.no_patients': 'No patients found',
  'patient.search_placeholder': 'Search by code, diagnosis, or cancer type...',
  'patient.detail_title': 'Patient Detail',
  'patient.demographics': 'Demographics',
  'patient.clinical_info': 'Clinical Information',
  'patient.variants_section': 'Variants',
  'patient.treatments_section': 'Treatments',
  'patient.reports_section': 'Reports',

  // Variants
  'variant.title': 'Variant Browser',
  'variant.gene': 'Gene',
  'variant.type': 'Type',
  'variant.somatic': 'Somatic',
  'variant.germline': 'Germline',
  'variant.hgvs_c': 'HGVS.c',
  'variant.hgvs_p': 'HGVS.p',
  'variant.vaf': 'VAF',
  'variant.consequence': 'Consequence',
  'variant.impact': 'Impact',
  'variant.acmg_tier': 'ACMG Tier',
  'variant.amp_level': 'AMP/ASCO/CAP',
  'variant.clinical_sig': 'Clinical Significance',
  'variant.cosmic': 'COSMIC',
  'variant.chromosome': 'Chr',
  'variant.position': 'Position',
  'variant.ref_alt': 'Ref / Alt',
  'variant.read_depth': 'Read Depth',
  'variant.filter_gene': 'Filter by gene...',
  'variant.no_variants': 'No variants found',
  'variant.detail_title': 'Variant Detail',

  // ACMG
  'acmg.title': 'ACMG Classification',
  'acmg.classification': 'Classification',
  'acmg.score': 'Score',
  'acmg.criteria': 'Criteria',
  'acmg.evidence': 'Evidence Summary',
  'acmg.pathogenic': 'Pathogenic',
  'acmg.likely_pathogenic': 'Likely Pathogenic',
  'acmg.uncertain': 'VUS',
  'acmg.likely_benign': 'Likely Benign',
  'acmg.benign': 'Benign',
  'acmg.classify': 'Run Classification',

  // Report
  'report.title': 'Reports',
  'report.generate': 'Generate Report',
  'report.status': 'Status',
  'report.type': 'Type',
  'report.generated_at': 'Generated',
  'report.download_md': 'Download Markdown',
  'report.download_json': 'Download JSON',
  'report.download_pdf': 'Download PDF',
  'report.generating': 'Generating report...',
  'report.no_reports': 'No reports generated yet',

  // Treatment
  'treatment.title': 'Treatment History',
  'treatment.name': 'Treatment',
  'treatment.type': 'Type',
  'treatment.target': 'Target',
  'treatment.start': 'Start Date',
  'treatment.end': 'End Date',
  'treatment.response': 'Response',
  'treatment.status': 'Status',
  'treatment.add': 'Add Treatment',
  'treatment.no_treatments': 'No treatment records',

  // Pipeline
  'pipeline.title': 'Pipeline Run',
  'pipeline.start': 'Run Pipeline',
  'pipeline.upload_vcf': 'Upload VCF File',
  'pipeline.select_patient': 'Select Patient',
  'pipeline.options': 'Pipeline Options',
  'pipeline.progress': 'Progress',
  'pipeline.phase': 'Phase',
  'pipeline.run_id': 'Run ID',
  'pipeline.results': 'Results',
  'pipeline.status_queued': 'Queued',
  'pipeline.status_running': 'Running',
  'pipeline.status_completed': 'Completed',
  'pipeline.status_failed': 'Failed',

  // Gene
  'gene.title': 'Gene View',
  'gene.name': 'Gene Name',
  'gene.full_name': 'Full Name',
  'gene.oncogene_type': 'Oncogene Type',
  'gene.cosmic_tier': 'COSMIC Tier',
  'gene.hotspot': 'Hotspot',
  'gene.drugs': 'Targeted Drugs',
  'gene.cancers': 'Associated Cancers',
  'gene.description': 'Description',

  // Settings
  'settings.title': 'System Settings',
  'settings.general': 'General',
  'settings.appearance': 'Appearance',
  'settings.language': 'Language',
  'settings.database': 'Database',
  'settings.api': 'API Configuration',
  'settings.modules': 'Module Management',
  'settings.save_success': 'Settings saved successfully',
  'settings.save_error': 'Failed to save settings',

  // Dashboard
  'dashboard.title': 'OpenPanCan',
  'dashboard.subtitle': 'Pancreatic Cancer Genomic Analysis',
  'dashboard.welcome': 'Welcome to OpenPanCan',
  'dashboard.total_patients': 'Total Patients',
  'dashboard.total_variants': 'Total Variants',
  'dashboard.total_reports': 'Reports Generated',
  'dashboard.total_treatments': 'Treatment Records',
  'dashboard.recent_patients': 'Recent Patients',
  'dashboard.module_status': 'Module Status',
  'dashboard.tier_distribution': 'ACMG Tier Distribution',
  'dashboard.quick_links': 'Quick Links',
  'dashboard.new_analysis': 'New Analysis',
  'dashboard.browse_patients': 'Browse Patients',
  'dashboard.view_reports': 'View Reports',

  // Biomarker
  'biomarker.title': 'Biomarker Panel',
  'biomarker.kras': 'KRAS',
  'biomarker.tp53': 'TP53',
  'biomarker.smad4': 'SMAD4',
  'biomarker.cdkn2a': 'CDKN2A',
  'biomarker.brca1': 'BRCA1',
  'biomarker.brca2': 'BRCA2',
  'biomarker.positive': 'Positive',
  'biomarker.negative': 'Negative',
  'biomarker.unknown': 'Unknown',
  'biomarker.pending': 'Pending',

  // Module Status
  'module.online': 'Online',
  'module.offline': 'Offline',
  'module.degraded': 'Degraded',
  'module.vep': 'VEP Service',
  'module.phenotype_rag': 'Phenotype RAG',
  'module.phenotype_score': 'Phenotype Score',
  'module.ppi_score': 'PPI Score',
  'module.variant_rank': 'Variant Rank',
  'module.report': 'Report Service',
  'module.pancancer_system': 'PanCancerSystem',
};

const zh: TranslationMap = {
  // Navigation
  'nav.dashboard': '仪表盘',
  'nav.patients': '患者管理',
  'nav.variants': '变异浏览',
  'nav.reports': '报告',
  'nav.pipeline': '分析流程',
  'nav.settings': '设置',
  'nav.gene': '基因',

  // Common
  'common.loading': '加载中...',
  'common.error': '错误',
  'common.save': '保存',
  'common.cancel': '取消',
  'common.delete': '删除',
  'common.edit': '编辑',
  'common.create': '创建',
  'common.search': '搜索',
  'common.filter': '筛选',
  'common.export': '导出',
  'common.download': '下载',
  'common.refresh': '刷新',
  'common.back': '返回',
  'common.next': '下一步',
  'common.previous': '上一步',
  'common.confirm': '确认',
  'common.no_data': '暂无数据',
  'common.actions': '操作',
  'common.status': '状态',
  'common.details': '详情',
  'common.close': '关闭',
  'common.yes': '是',
  'common.no': '否',

  // Patients
  'patient.title': '癌症患者',
  'patient.create': '添加患者',
  'patient.code': '患者编号',
  'patient.age': '年龄',
  'patient.gender': '性别',
  'patient.diagnosis': '诊断',
  'patient.cancer_type': '癌症类型',
  'patient.stage': '分期',
  'patient.tumor_site': '肿瘤部位',
  'patient.survival': '生存状态',
  'patient.created': '创建时间',
  'patient.no_patients': '未找到患者',
  'patient.search_placeholder': '按编号、诊断或癌症类型搜索...',
  'patient.detail_title': '患者详情',
  'patient.demographics': '人口统计',
  'patient.clinical_info': '临床信息',
  'patient.variants_section': '变异信息',
  'patient.treatments_section': '治疗记录',
  'patient.reports_section': '报告',

  // Variants
  'variant.title': '变异浏览器',
  'variant.gene': '基因',
  'variant.type': '类型',
  'variant.somatic': '体细胞',
  'variant.germline': '胚系',
  'variant.hgvs_c': 'HGVS.c',
  'variant.hgvs_p': 'HGVS.p',
  'variant.vaf': '等位基因频率',
  'variant.consequence': '后果',
  'variant.impact': '影响',
  'variant.acmg_tier': 'ACMG 等级',
  'variant.amp_level': 'AMP/ASCO/CAP',
  'variant.clinical_sig': '临床意义',
  'variant.cosmic': 'COSMIC',
  'variant.chromosome': '染色体',
  'variant.position': '位置',
  'variant.ref_alt': '参考/替代',
  'variant.read_depth': '测序深度',
  'variant.filter_gene': '按基因筛选...',
  'variant.no_variants': '未发现变异',
  'variant.detail_title': '变异详情',

  // ACMG
  'acmg.title': 'ACMG 分类',
  'acmg.classification': '分类',
  'acmg.score': '评分',
  'acmg.criteria': '标准',
  'acmg.evidence': '证据摘要',
  'acmg.pathogenic': '致病',
  'acmg.likely_pathogenic': '可能致病',
  'acmg.uncertain': '意义不明确',
  'acmg.likely_benign': '可能良性',
  'acmg.benign': '良性',
  'acmg.classify': '运行分类',

  // Report
  'report.title': '报告',
  'report.generate': '生成报告',
  'report.status': '状态',
  'report.type': '类型',
  'report.generated_at': '生成时间',
  'report.download_md': '下载 Markdown',
  'report.download_json': '下载 JSON',
  'report.download_pdf': '下载 PDF',
  'report.generating': '正在生成报告...',
  'report.no_reports': '暂无生成报告',

  // Treatment
  'treatment.title': '治疗历史',
  'treatment.name': '治疗方案',
  'treatment.type': '类型',
  'treatment.target': '靶点',
  'treatment.start': '开始日期',
  'treatment.end': '结束日期',
  'treatment.response': '疗效',
  'treatment.status': '状态',
  'treatment.add': '添加治疗记录',
  'treatment.no_treatments': '暂无治疗记录',

  // Pipeline
  'pipeline.title': '分析流程',
  'pipeline.start': '运行流程',
  'pipeline.upload_vcf': '上传 VCF 文件',
  'pipeline.select_patient': '选择患者',
  'pipeline.options': '流程选项',
  'pipeline.progress': '进度',
  'pipeline.phase': '阶段',
  'pipeline.run_id': '运行 ID',
  'pipeline.results': '结果',
  'pipeline.status_queued': '排队中',
  'pipeline.status_running': '运行中',
  'pipeline.status_completed': '已完成',
  'pipeline.status_failed': '失败',

  // Gene
  'gene.title': '基因视图',
  'gene.name': '基因名称',
  'gene.full_name': '全称',
  'gene.oncogene_type': '致癌基因类型',
  'gene.cosmic_tier': 'COSMIC 等级',
  'gene.hotspot': '热点',
  'gene.drugs': '靶向药物',
  'gene.cancers': '相关癌症',
  'gene.description': '描述',

  // Settings
  'settings.title': '系统设置',
  'settings.general': '通用',
  'settings.appearance': '外观',
  'settings.language': '语言',
  'settings.database': '数据库',
  'settings.api': 'API 配置',
  'settings.modules': '模块管理',
  'settings.save_success': '设置保存成功',
  'settings.save_error': '设置保存失败',

  // Dashboard
  'dashboard.title': 'OpenPanCan',
  'dashboard.subtitle': '胰腺癌基因组分析',
  'dashboard.welcome': '欢迎使用 OpenPanCan',
  'dashboard.total_patients': '患者总数',
  'dashboard.total_variants': '变异总数',
  'dashboard.total_reports': '已生成报告',
  'dashboard.total_treatments': '治疗记录',
  'dashboard.recent_patients': '最近患者',
  'dashboard.module_status': '模块状态',
  'dashboard.tier_distribution': 'ACMG 等级分布',
  'dashboard.quick_links': '快捷操作',
  'dashboard.new_analysis': '新建分析',
  'dashboard.browse_patients': '浏览患者',
  'dashboard.view_reports': '查看报告',

  // Biomarker
  'biomarker.title': '生物标志物面板',
  'biomarker.kras': 'KRAS',
  'biomarker.tp53': 'TP53',
  'biomarker.smad4': 'SMAD4',
  'biomarker.cdkn2a': 'CDKN2A',
  'biomarker.brca1': 'BRCA1',
  'biomarker.brca2': 'BRCA2',
  'biomarker.positive': '阳性',
  'biomarker.negative': '阴性',
  'biomarker.unknown': '未知',
  'biomarker.pending': '待定',

  // Module Status
  'module.online': '在线',
  'module.offline': '离线',
  'module.degraded': '降级',
  'module.vep': 'VEP 服务',
  'module.phenotype_rag': '表型 RAG',
  'module.phenotype_score': '表型评分',
  'module.ppi_score': 'PPI 评分',
  'module.variant_rank': '变异排序',
  'module.report': '报告服务',
  'module.pancancer_system': 'PanCancerSystem',
};

const translations: Record<Language, TranslationMap> = { en, zh };

/** Get a translation by key with optional language override */
export function t(key: string, lang?: Language): string {
  const locale = lang || ((typeof window !== 'undefined' &&
    (localStorage.getItem('openpancan-lang') as Language)) || 'en');
  return translations[locale]?.[key] || translations.en[key] || key;
}

/** Set the preferred language */
export function setLanguage(lang: Language): void {
  if (typeof window !== 'undefined') {
    localStorage.setItem('openpancan-lang', lang);
  }
}

/** Get the current language */
export function getLanguage(): Language {
  if (typeof window !== 'undefined') {
    return (localStorage.getItem('openpancan-lang') as Language) || 'en';
  }
  return 'en';
}

export default { t, setLanguage, getLanguage };
