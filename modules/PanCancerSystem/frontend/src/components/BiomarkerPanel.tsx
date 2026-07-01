import type { SomaticVariant, GermlineVariant } from '@/types';
import { t } from '@/i18n';

// =============================================================================
// Biomarker Panel Component
// =============================================================================
//
// Displays the status of key pancreatic cancer biomarker genes
// (KRAS, TP53, SMAD4, CDKN2A, BRCA1/2) based on detected variants.
//
// Props:
//   variants - Array of somatic variants
//   germlineVariants - Array of germline variants (for BRCA1/2)
//
// =============================================================================

interface BiomarkerPanelProps {
  variants: SomaticVariant[];
  germlineVariants?: GermlineVariant[];
}

interface BiomarkerGene {
  gene: string;
  label: string;
  description: string;
  type: 'somatic' | 'germline' | 'both';
  clinicalAction: string;
}

const BIOMARKER_GENES: BiomarkerGene[] = [
  {
    gene: 'KRAS',
    label: 'biomarker.kras',
    description: 'Most common oncogene in PDAC. G12D/V/R mutations drive tumorigenesis. KRAS G12C mutations may respond to sotorasib.',
    type: 'somatic',
    clinicalAction: 'KRAS G12C: consider sotorasib. Other mutations: no targeted therapy yet, but important for prognosis.',
  },
  {
    gene: 'TP53',
    label: 'biomarker.tp53',
    description: 'Tumor suppressor. Loss-of-function mutations in ~75% of PDAC. Associated with poor prognosis and genomic instability.',
    type: 'somatic',
    clinicalAction: 'No direct targeted therapy. Consider platinum-based chemotherapy for TP53-mutated tumors.',
  },
  {
    gene: 'SMAD4',
    label: 'biomarker.smad4',
    description: 'TGF-β pathway tumor suppressor. Loss in ~55% of PDAC. Associated with metastatic progression.',
    type: 'somatic',
    clinicalAction: 'SMAD4 loss associated with worse prognosis and metastatic spread. No direct targeted therapy.',
  },
  {
    gene: 'CDKN2A',
    label: 'biomarker.cdkn2a',
    description: 'Cell cycle regulator (p16). Loss in >80% of PDAC. Potential biomarker for CDK4/6 inhibitor response.',
    type: 'somatic',
    clinicalAction: 'CDKN2A loss may indicate sensitivity to CDK4/6 inhibitors (palbociclib, ribociclib) in clinical trials.',
  },
  {
    gene: 'BRCA1',
    label: 'biomarker.brca1',
    description: 'DNA repair gene. Germline or somatic mutations may indicate PARP inhibitor sensitivity.',
    type: 'both',
    clinicalAction: 'BRCA1 mutations: consider PARP inhibitors (olaparib). Platinum sensitivity may be increased.',
  },
  {
    gene: 'BRCA2',
    label: 'biomarker.brca2',
    description: 'DNA repair gene. Mutations indicate HRD and PARP inhibitor sensitivity. Most common HRD gene in PDAC.',
    type: 'both',
    clinicalAction: 'BRCA2 mutations: FDA-approved olaparib maintenance. Strong platinum sensitivity.',
  },
];

export default function BiomarkerPanel({ variants, germlineVariants = [] }: BiomarkerPanelProps) {
  const getGeneStatus = (gene: string): {
    status: 'positive' | 'negative' | 'unknown';
    variantCount: number;
    keyMutation?: string;
  } => {
    const somaticHits = variants.filter((v) => v.gene === gene);
    const germlineHits = germlineVariants.filter((v) => v.gene === gene);
    const allHits = [...somaticHits, ...germlineHits.map((v) => ({ ...v, hgvs_p: v.hgvs_p } as SomaticVariant))];

    if (allHits.length > 0) {
      return {
        status: 'positive',
        variantCount: allHits.length,
        keyMutation: allHits[0].hgvs_p || undefined,
      };
    }
    return { status: 'negative', variantCount: 0 };
  };

  const getStatusStyles = (status: string) => {
    switch (status) {
      case 'positive':
        return {
          dot: 'status-dot-green',
          badge: 'badge-green',
          text: 'text-green-700',
          bg: 'bg-green-50 border-green-200',
        };
      case 'negative':
        return {
          dot: 'status-dot-gray',
          badge: 'badge-gray',
          text: 'text-gray-500',
          bg: 'bg-gray-50 border-gray-200',
        };
      default:
        return {
          dot: 'status-dot-amber',
          badge: 'badge-amber',
          text: 'text-amber-700',
          bg: 'bg-amber-50 border-amber-200',
        };
    }
  };

  const positiveCount = BIOMARKER_GENES.filter(
    (bg) => getGeneStatus(bg.gene).status === 'positive'
  ).length;

  return (
    <div className="card animate-fade-in">
      <div className="card-header">
        <div>
          <h3 className="font-semibold text-gray-900">{t('biomarker.title')}</h3>
          <p className="text-xs text-gray-400 mt-0.5">
            {positiveCount}/{BIOMARKER_GENES.length} genes altered
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="flex items-center gap-1 text-xs text-green-600">
            <span className="status-dot-green" /> {t('biomarker.positive')}
          </span>
          <span className="flex items-center gap-1 text-xs text-gray-400">
            <span className="status-dot-gray" /> {t('biomarker.negative')}
          </span>
        </div>
      </div>

      <div className="card-body">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {BIOMARKER_GENES.map((bg) => {
            const { status, variantCount, keyMutation } = getGeneStatus(bg.gene);
            const styles = getStatusStyles(status);

            return (
              <div
                key={bg.gene}
                className={`rounded-xl border p-4 transition-all duration-200 hover:shadow-card ${styles.bg}`}
              >
                {/* Gene name + status */}
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <h4 className="font-bold text-gray-900">{bg.gene}</h4>
                    <p className="text-2xs text-gray-400">{t(bg.label) || bg.gene}</p>
                  </div>
                  <span className={`badge text-2xs ${styles.badge}`}>
                    {status === 'positive'
                      ? t('biomarker.positive')
                      : t('biomarker.negative')}
                  </span>
                </div>

                {/* Key mutation */}
                {keyMutation && (
                  <div className="mb-3">
                    <span className="inline-block px-2 py-0.5 bg-white/80 rounded text-xs font-mono text-gray-800 border border-gray-200">
                      {keyMutation}
                    </span>
                    {variantCount > 1 && (
                      <span className="text-2xs text-gray-500 ml-1">+{variantCount - 1} more</span>
                    )}
                  </div>
                )}

                {/* Description */}
                <p className="text-xs text-gray-600 leading-relaxed mb-3">
                  {bg.description}
                </p>

                {/* Clinical action */}
                <div className={`text-2xs p-2 rounded-lg ${
                  status === 'positive'
                    ? 'bg-white/60 text-green-800'
                    : 'bg-white/40 text-gray-500'
                }`}>
                  <span className="font-semibold">Clinical Action: </span>
                  {bg.clinicalAction}
                </div>

                {/* Variant count */}
                {status === 'positive' && (
                  <div className="mt-2 pt-2 border-t border-green-200/50 flex items-center justify-between text-2xs">
                    <span className="text-green-600">
                      {variantCount} variant{variantCount > 1 ? 's' : ''} detected
                    </span>
                    <span className="text-green-500">
                      {bg.type === 'somatic' ? 'Somatic' : bg.type === 'germline' ? 'Germline' : 'Somatic + Germline'}
                    </span>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
