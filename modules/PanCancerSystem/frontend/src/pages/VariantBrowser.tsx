import { useEffect, useState, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { variantBrowserAPI, somaticVariantsAPI, germlineVariantsAPI } from '@/services/api';
import { useUIStore } from '@/store';
import { t } from '@/i18n';
import type { SomaticVariant, GermlineVariant } from '@/types';

// =============================================================================
// Variant Browser Page
// =============================================================================

export default function VariantBrowser() {
  const { patientId } = useParams<{ patientId?: string }>();
  const { language } = useUIStore();

  const [variants, setVariants] = useState<(SomaticVariant | GermlineVariant)[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  // Filters
  const [geneFilter, setGeneFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState<'all' | 'somatic' | 'germline'>('all');
  const [tierFilter, setTierFilter] = useState<string>('all');

  const loadVariants = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      if (patientId) {
        // Load variants for specific patient
        const params = {
          gene: geneFilter || undefined,
          page,
          page_size: 50,
        };
        const [somatic, germline] = await Promise.all([
          typeFilter === 'all' || typeFilter === 'somatic'
            ? somaticVariantsAPI.list(patientId, params).catch(() => ({ items: [], total: 0, page: 1, page_size: 50, total_pages: 0 }))
            : { items: [], total: 0, page: 1, page_size: 50, total_pages: 0 },
          typeFilter === 'all' || typeFilter === 'germline'
            ? germlineVariantsAPI.list(patientId, { gene: geneFilter || undefined, page, page_size: 50 }).catch(() => ({ items: [], total: 0, page: 1, page_size: 50, total_pages: 0 }))
            : { items: [], total: 0, page: 1, page_size: 50, total_pages: 0 },
        ]);
        const all = [...somatic.items, ...germline.items];
        setVariants(all);
        setTotalPages(Math.max(somatic.total_pages, germline.total_pages));
      } else {
        const response = await variantBrowserAPI.search({
          gene: geneFilter || undefined,
          type: typeFilter === 'all' ? undefined : typeFilter,
          acmg_tier: tierFilter === 'all' ? undefined : tierFilter,
          page,
          page_size: 50,
        });
        setVariants(response.items);
        setTotalPages(response.total_pages);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load variants');
    } finally {
      setLoading(false);
    }
  }, [patientId, geneFilter, typeFilter, tierFilter, page]);

  useEffect(() => {
    loadVariants();
  }, [loadVariants]);

  const isSomatic = (v: SomaticVariant | GermlineVariant): v is SomaticVariant =>
    'variant_allele_frequency' in v;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{t('variant.title')}</h1>
          {patientId && (
            <p className="text-sm text-gray-500 mt-1">
              <Link to={`/patients/${patientId}`} className="text-primary-600 hover:underline">
                Patient {patientId}
              </Link>
            </p>
          )}
        </div>
        <button onClick={loadVariants} className="btn-secondary" title={t('common.refresh')}>
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </button>
      </div>

      {/* Filters */}
      <div className="card p-4">
        <div className="flex flex-wrap gap-3 items-end">
          <div className="flex-1 min-w-[200px]">
            <label className="label">{t('variant.gene')}</label>
            <input
              className="input"
              placeholder={t('variant.filter_gene')}
              value={geneFilter}
              onChange={(e) => { setGeneFilter(e.target.value); setPage(1); }}
            />
          </div>
          <div>
            <label className="label">{t('variant.type')}</label>
            <select
              className="input"
              value={typeFilter}
              onChange={(e) => { setTypeFilter(e.target.value as 'all' | 'somatic' | 'germline'); setPage(1); }}
            >
              <option value="all">All Types</option>
              <option value="somatic">{t('variant.somatic')}</option>
              <option value="germline">{t('variant.germline')}</option>
            </select>
          </div>
          <div>
            <label className="label">{t('variant.acmg_tier')}</label>
            <select
              className="input"
              value={tierFilter}
              onChange={(e) => { setTierFilter(e.target.value); setPage(1); }}
            >
              <option value="all">All Tiers</option>
              <option value="I">Tier I</option>
              <option value="II">Tier II</option>
              <option value="III">Tier III</option>
              <option value="IV">Tier IV</option>
            </select>
          </div>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="p-4 bg-red-50 text-red-700 rounded-lg text-sm">{error}</div>
      )}

      {/* Table */}
      {loading ? (
        <div className="space-y-3">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="skeleton h-12 rounded-lg" />
          ))}
        </div>
      ) : variants.length === 0 ? (
        <div className="card p-12 text-center">
          <svg className="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1}
              d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          <p className="text-gray-500 text-sm">{t('variant.no_variants')}</p>
        </div>
      ) : (
        <>
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>{t('variant.gene')}</th>
                  <th>{t('variant.type')}</th>
                  <th>{t('variant.hgvs_p')}</th>
                  <th>{t('variant.vaf')}</th>
                  <th>{t('variant.consequence')}</th>
                  <th>{t('variant.acmg_tier')}</th>
                  <th>{t('variant.clinical_sig')}</th>
                </tr>
              </thead>
              <tbody>
                {variants.map((v) => {
                  const somatic = isSomatic(v);
                  return (
                    <tr key={v.id} className="hover:bg-blue-50/30">
                      <td>
                        <span className="font-medium text-primary-700">{v.gene}</span>
                      </td>
                      <td>
                        <span className={`badge text-2xs ${somatic ? 'badge-blue' : 'badge-purple'}`}>
                          {somatic ? t('variant.somatic') : t('variant.germline')}
                        </span>
                      </td>
                      <td className="font-mono text-xs text-gray-600 max-w-[200px] truncate">
                        {v.hgvs_p || '-'}
                      </td>
                      <td>
                        {somatic ? (
                          <span className={somatic && v.variant_allele_frequency > 0.3 ? 'text-amber-600 font-medium' : 'text-gray-600'}>
                            {(v.variant_allele_frequency * 100).toFixed(1)}%
                          </span>
                        ) : '-'}
                      </td>
                      <td className="text-xs text-gray-500 max-w-[200px] truncate">
                        {somatic ? (v.consequence || '-') : '-'}
                      </td>
                      <td>
                        {somatic && v.acmg_tier ? (
                          <span className={`badge text-xs font-bold ${getTierBadge(v.acmg_tier)}`}>
                            {v.acmg_tier}
                          </span>
                        ) : (
                          <span className="text-gray-400">-</span>
                        )}
                      </td>
                      <td className="text-xs">
                        {'clinical_significance' in v && v.clinical_significance ? (
                          <span className="badge-gray">{v.clinical_significance}</span>
                        ) : somatic && v.clinical_significance ? (
                          <span className="badge-gray">{v.clinical_significance}</span>
                        ) : (
                          '-'
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between">
              <p className="text-sm text-gray-500">Page {page} of {totalPages}</p>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1}
                  className="btn-secondary btn-sm"
                >
                  {t('common.previous')}
                </button>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page >= totalPages}
                  className="btn-secondary btn-sm"
                >
                  {t('common.next')}
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function getTierBadge(tier: string): string {
  switch (tier) {
    case 'I': return 'badge-green';
    case 'II': return 'badge-blue';
    case 'III': return 'badge-amber';
    case 'IV': return 'badge-red';
    default: return 'badge-gray';
  }
}
