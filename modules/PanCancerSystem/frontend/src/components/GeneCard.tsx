import type { GeneInfo } from '@/types';

// =============================================================================
// Gene Card Component
// =============================================================================
//
// Displays comprehensive gene information including COSMIC data,
// oncogenic classification, hotspot mutations, and targeted drugs.
//
// Props:
//   gene - GeneInfo object with all gene details
//   compact - Render in compact mode
//
// =============================================================================

interface GeneCardProps {
  gene: GeneInfo;
  compact?: boolean;
}

export default function GeneCard({ gene, compact = false }: GeneCardProps) {
  const oncogeneColors: Record<string, string> = {
    oncogene: 'badge-red',
    tumor_suppressor: 'badge-blue',
    both: 'badge-purple',
    unknown: 'badge-gray',
  };

  const cosmicTierColors: Record<number, string> = {
    1: 'bg-red-100 text-red-800',
    2: 'bg-amber-100 text-amber-800',
    3: 'bg-gray-100 text-gray-600',
  };

  if (compact) {
    return (
      <div className="card p-4 hover:shadow-card transition-shadow">
        <div className="flex items-start justify-between">
          <div>
            <h3 className="font-bold text-gray-900">{gene.gene_name}</h3>
            <p className="text-xs text-gray-500">{gene.full_name}</p>
          </div>
          <div className="flex gap-1">
            <span className={`badge text-2xs ${oncogeneColors[gene.oncogene_type] || 'badge-gray'}`}>
              {gene.oncogene_type.replace('_', ' ')}
            </span>
            {gene.is_hotspot && (
              <span className="badge badge-amber text-2xs">Hotspot</span>
            )}
          </div>
        </div>
        <div className="mt-2 flex items-center gap-2 text-xs text-gray-500">
          <span>COSMIC Tier: {gene.cosmic_tier}</span>
          <span>•</span>
          <span>{gene.associated_cancers.length} cancers</span>
          <span>•</span>
          <span>{gene.targeted_drugs.length} drugs</span>
        </div>
      </div>
    );
  }

  return (
    <div className="card animate-fade-in">
      {/* Header */}
      <div className="card-header">
        <div>
          <h2 className="text-lg font-bold text-gray-900">{gene.gene_name}</h2>
          <p className="text-sm text-gray-500">{gene.full_name}</p>
        </div>
        <div className="flex gap-2">
          <span className={`badge ${oncogeneColors[gene.oncogene_type] || 'badge-gray'}`}>
            {gene.oncogene_type.replace('_', ' ')}
          </span>
          {gene.is_hotspot && (
            <span className="badge badge-amber">🔥 Hotspot</span>
          )}
        </div>
      </div>

      <div className="card-body space-y-6">
        {/* Key info grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <p className="text-2xl font-bold text-gray-900">{gene.chromosome}</p>
            <p className="text-xs text-gray-500 mt-1">Chromosome</p>
          </div>
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <p className={`text-2xl font-bold ${cosmicTierColors[gene.cosmic_tier] || 'text-gray-900'}`}>
              {gene.cosmic_tier}
            </p>
            <p className="text-xs text-gray-500 mt-1">COSMIC Tier</p>
          </div>
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <p className="text-2xl font-bold text-gray-900">{gene.associated_cancers.length}</p>
            <p className="text-xs text-gray-500 mt-1">Cancer Types</p>
          </div>
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <p className="text-2xl font-bold text-gray-900">{gene.targeted_drugs.length}</p>
            <p className="text-xs text-gray-500 mt-1">Targeted Drugs</p>
          </div>
        </div>

        {/* Description */}
        {gene.description && (
          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-2">Description</h3>
            <p className="text-sm text-gray-600 leading-relaxed">{gene.description}</p>
          </div>
        )}

        {/* Oncogenic classification */}
        <div>
          <h3 className="text-sm font-semibold text-gray-700 mb-2">Oncogenic Classification</h3>
          <div className="flex items-center gap-2">
            <span className={`badge text-sm ${
              gene.oncokb_oncogenic === 'Oncogenic' ? 'badge-red' :
              gene.oncokb_oncogenic === 'Likely Oncogenic' ? 'badge-amber' :
              'badge-gray'
            }`}>
              {gene.oncokb_oncogenic || 'Unknown'}
            </span>
            <span className="text-xs text-gray-400">via OncoKB</span>
          </div>
        </div>

        {/* Hotspot mutations */}
        {gene.hotspot_mutations.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-3">
              Hotspot Mutations ({gene.hotspot_mutations.length})
            </h3>
            <div className="table-container">
              <table className="table">
                <thead>
                  <tr>
                    <th>Position</th>
                    <th>AA Change</th>
                    <th>Frequency</th>
                    <th>Oncogenic</th>
                  </tr>
                </thead>
                <tbody>
                  {gene.hotspot_mutations.map((hm, i) => (
                    <tr key={i}>
                      <td className="font-mono text-xs">{hm.position}</td>
                      <td className="font-mono text-xs font-medium">{hm.aa_change}</td>
                      <td>
                        <div className="flex items-center gap-2">
                          <div className="w-16 bg-gray-100 rounded-full h-1.5">
                            <div
                              className="bg-primary-500 h-1.5 rounded-full"
                              style={{ width: `${Math.min(hm.frequency * 100, 100)}%` }}
                            />
                          </div>
                          <span className="text-xs text-gray-500">{(hm.frequency * 100).toFixed(1)}%</span>
                        </div>
                      </td>
                      <td>
                        <span className={`badge text-2xs ${
                          hm.oncogenic === 'Oncogenic' ? 'badge-red' : 'badge-gray'
                        }`}>
                          {hm.oncogenic}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Targeted drugs */}
        {gene.targeted_drugs.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-3">
              Targeted Drugs ({gene.targeted_drugs.length})
            </h3>
            <div className="table-container">
              <table className="table">
                <thead>
                  <tr>
                    <th>Drug</th>
                    <th>Target</th>
                    <th>Biomarker</th>
                    <th>Approval</th>
                    <th>Efficacy</th>
                  </tr>
                </thead>
                <tbody>
                  {gene.targeted_drugs.map((drug, i) => (
                    <tr key={i}>
                      <td className="font-medium text-primary-700">{drug.drug_name}</td>
                      <td className="text-xs">{drug.target}</td>
                      <td className="text-xs">{drug.biomarker}</td>
                      <td>
                        <span className={`badge text-2xs ${
                          drug.approval_status === 'FDA Approved' ? 'badge-green' : 'badge-amber'
                        }`}>
                          {drug.approval_status}
                        </span>
                      </td>
                      <td className="text-xs text-gray-600">{drug.efficacy || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Associated cancers */}
        {gene.associated_cancers.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-2">Associated Cancers</h3>
            <div className="flex flex-wrap gap-1.5">
              {gene.associated_cancers.map((cancer, i) => (
                <span key={i} className="badge-blue text-xs">{cancer}</span>
              ))}
            </div>
          </div>
        )}

        {/* Citations count */}
        {gene.citations.length > 0 && (
          <div className="text-xs text-gray-400">
            {gene.citations.length} citation{gene.citations.length > 1 ? 's' : ''}
          </div>
        )}
      </div>
    </div>
  );
}
