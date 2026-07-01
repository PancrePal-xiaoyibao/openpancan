import type { SomaticVariant } from '@/types';

// =============================================================================
// Tumor Molecular Profile Component
// =============================================================================
//
// Displays a comprehensive tumor molecular profile summary based on
// somatic variants, showing key metrics and distributions.
//
// Props:
//   variants - Array of somatic variants for the tumor
//
// =============================================================================

interface TumorProfileProps {
  variants: SomaticVariant[];
}

// Pancreatic cancer driver genes
const DRIVER_GENES = [
  'KRAS', 'TP53', 'SMAD4', 'CDKN2A', 'ARID1A', 'GNAS',
  'RNF43', 'TGFBR2', 'RB1', 'PIK3CA', 'BRAF', 'BRCA1',
  'BRCA2', 'PALB2', 'ATM', 'STK11', 'CTNNB1', 'MAP2K4',
];

export default function TumorProfile({ variants }: TumorProfileProps) {
  // Computed metrics
  const totalVariants = variants.length;
  const driverVariants = variants.filter((v) => DRIVER_GENES.includes(v.gene));
  const highVAF = variants.filter((v) => v.variant_allele_frequency > 0.3);
  const cosmicAnnotated = variants.filter((v) => v.cosmic_id);
  const tiered = variants.filter((v) => v.acmg_tier);
  const tierDistribution = {
    I: variants.filter((v) => v.acmg_tier === 'I').length,
    II: variants.filter((v) => v.acmg_tier === 'II').length,
    III: variants.filter((v) => v.acmg_tier === 'III').length,
    IV: variants.filter((v) => v.acmg_tier === 'IV').length,
  };
  const untiered = totalVariants - tiered.length;

  // Top mutated genes
  const geneCount: Record<string, number> = {};
  variants.forEach((v) => {
    geneCount[v.gene] = (geneCount[v.gene] || 0) + 1;
  });
  const topGenes = Object.entries(geneCount)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8);

  // Impact distribution
  const impactDist: Record<string, number> = {};
  variants.forEach((v) => {
    if (v.impact) {
      impactDist[v.impact] = (impactDist[v.impact] || 0) + 1;
    }
  });

  return (
    <div className="card animate-fade-in">
      <div className="card-header">
        <h3 className="font-semibold text-gray-900">Tumor Molecular Profile</h3>
        <span className="text-xs text-gray-400">{totalVariants} variants</span>
      </div>

      <div className="card-body space-y-6">
        {/* Key Metrics */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <MetricCard
            label="Total Variants"
            value={totalVariants}
            color="text-gray-900"
          />
          <MetricCard
            label="In Driver Genes"
            value={driverVariants.length}
            sub={`${DRIVER_GENES.length} genes`}
            color="text-primary-600"
          />
          <MetricCard
            label="High VAF (>30%)"
            value={highVAF.length}
            sub={`${totalVariants > 0 ? Math.round((highVAF.length / totalVariants) * 100) : 0}%`}
            color="text-amber-600"
          />
          <MetricCard
            label="COSMIC Annotated"
            value={cosmicAnnotated.length}
            sub={`${totalVariants > 0 ? Math.round((cosmicAnnotated.length / totalVariants) * 100) : 0}%`}
            color="text-purple-600"
          />
        </div>

        {/* ACMG Tier Distribution */}
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-3">ACMG Tier Distribution</h4>
          {totalVariants > 0 ? (
            <div className="space-y-3">
              {(['I', 'II', 'III', 'IV'] as const).map((tier) => {
                const count = tierDistribution[tier];
                const pct = Math.round((count / totalVariants) * 100);
                const colors: Record<string, string> = {
                  I: 'bg-tier-1',
                  II: 'bg-tier-2',
                  III: 'bg-tier-3',
                  IV: 'bg-tier-4',
                };
                return (
                  <div key={tier} className="flex items-center gap-3">
                    <span className={`badge text-xs w-8 justify-center bg-opacity-20`}
                      style={{ backgroundColor: `var(--tw-${colors[tier].replace('bg-', '')})` }}
                    >
                      {tier}
                    </span>
                    <div className="flex-1 bg-gray-100 rounded-full h-2.5">
                      <div
                        className={`h-2.5 rounded-full transition-all duration-700 ${colors[tier]}`}
                        style={{ width: `${Math.max(pct, 2)}%` }}
                      />
                    </div>
                    <span className="text-xs text-gray-500 w-8 text-right">{count}</span>
                    <span className="text-xs text-gray-400 w-10 text-right">{pct}%</span>
                  </div>
                );
              })}
              {untiered > 0 && (
                <div className="flex items-center gap-3">
                  <span className="badge-gray text-xs w-8 justify-center">—</span>
                  <div className="flex-1 bg-gray-100 rounded-full h-2.5">
                    <div
                      className="bg-gray-300 h-2.5 rounded-full"
                      style={{ width: `${Math.max(Math.round((untiered / totalVariants) * 100), 2)}%` }}
                    />
                  </div>
                  <span className="text-xs text-gray-500 w-8 text-right">{untiered}</span>
                  <span className="text-xs text-gray-400 w-10 text-right">{Math.round((untiered / totalVariants) * 100)}%</span>
                </div>
              )}
            </div>
          ) : (
            <p className="text-sm text-gray-400">No variants to display</p>
          )}
        </div>

        {/* Top Mutated Genes */}
        {topGenes.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-3">Top Mutated Genes</h4>
            <div className="flex flex-wrap gap-2">
              {topGenes.map(([gene, count]) => {
                const isDriver = DRIVER_GENES.includes(gene);
                return (
                  <div
                    key={gene}
                    className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border
                      ${isDriver
                        ? 'bg-primary-50 border-primary-200 text-primary-700'
                        : 'bg-gray-50 border-gray-200 text-gray-700'}`}
                  >
                    <span className="text-sm font-medium">{gene}</span>
                    <span className={`badge text-2xs ${isDriver ? 'badge-blue' : 'badge-gray'}`}>
                      {count}
                    </span>
                    {isDriver && <span className="text-2xs text-primary-400">driver</span>}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Impact Distribution */}
        {Object.keys(impactDist).length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-3">Variant Impact</h4>
            <div className="flex flex-wrap gap-2">
              {Object.entries(impactDist).map(([impact, count]) => (
                <span key={impact} className={`badge text-xs ${
                  impact === 'HIGH' ? 'badge-red' :
                  impact === 'MODERATE' ? 'badge-amber' :
                  'badge-gray'
                }`}>
                  {impact}: {count}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// =============================================================================
// Metric Card
// =============================================================================

function MetricCard({
  label,
  value,
  sub,
  color,
}: {
  label: string;
  value: number;
  sub?: string;
  color: string;
}) {
  return (
    <div className="bg-gray-50 rounded-lg p-4 text-center">
      <p className={`text-2xl font-bold ${color}`}>{value}</p>
      <p className="text-xs text-gray-500 mt-1">{label}</p>
      {sub && <p className="text-2xs text-gray-400 mt-0.5">{sub}</p>}
    </div>
  );
}
