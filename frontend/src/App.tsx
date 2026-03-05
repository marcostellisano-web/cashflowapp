import { useState } from 'react';
import HomePage from './components/HomePage';
import AppShell from './components/layout/AppShell';
import BudgetUploader from './components/upload/BudgetUploader';
import BudgetPreview from './components/upload/BudgetPreview';
import ParametersUploader from './components/parameters/ParametersUploader';
import ProductionForm from './components/parameters/ProductionForm';
import CurveAssigner from './components/distribution/CurveAssigner';
import DownloadButton from './components/output/DownloadButton';
import type { ParsedBudget } from './types/budget';
import type { ProductionParameters } from './types/production';
import type { LineItemDistribution, CashflowOutput } from './types/cashflow';
import { previewCashflow } from './lib/api';

type AppMode = 'home' | 'cashflow';

export default function App() {
  const [mode, setMode] = useState<AppMode>('home');
  const [step, setStep] = useState(0);
  const [budget, setBudget] = useState<ParsedBudget | null>(null);
  const [params, setParams] = useState<ProductionParameters | null>(null);
  const [paramsMode, setParamsMode] = useState<'choose' | 'manual'>('choose');
  const [distributions, setDistributions] = useState<LineItemDistribution[]>(
    [],
  );
  const [preview, setPreview] = useState<CashflowOutput | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState<string | null>(null);

  const handleGoHome = () => {
    setMode('home');
    setStep(0);
    setParamsMode('choose');
    setDistributions([]);
    setPreview(null);
    setPreviewError(null);
  };

  const handleBudgetParsed = (parsed: ParsedBudget) => {
    setBudget(parsed);
  };

  const handleParamsSubmit = (p: ProductionParameters) => {
    setParams(p);
    setStep(2);
  };

  const handleParamsUploaded = (p: ProductionParameters) => {
    setParams(p);
    setStep(2);
  };

  const handleDistributionsSubmit = async (dists: LineItemDistribution[]) => {
    setDistributions(dists);
    if (!budget || !params) return;

    setPreviewLoading(true);
    setPreviewError(null);
    setStep(3);

    try {
      const output = await previewCashflow(budget, params, dists);
      setPreview(output);
    } catch (e: any) {
      setPreviewError(e.message || 'Failed to generate preview');
    } finally {
      setPreviewLoading(false);
    }
  };

  if (mode === 'home') {
    return <HomePage onSelectCashflow={() => setMode('cashflow')} onBudgetParsed={handleBudgetParsed} initialBudget={budget} />;
  }

  return (
    <AppShell currentStep={step} onHome={handleGoHome}>
      {/* Step 0: Upload */}
      {step === 0 && !budget && (
        <BudgetUploader onParsed={handleBudgetParsed} />
      )}
      {step === 0 && budget && (
        <BudgetPreview
          budget={budget}
          onNext={() => setStep(1)}
          onReset={() => setBudget(null)}
        />
      )}

      {/* Step 1: Production Parameters — choose mode or manual form */}
      {step === 1 && paramsMode === 'choose' && (
        <ParametersUploader
          existingParams={params}
          onParsed={handleParamsUploaded}
          onManual={() => setParamsMode('manual')}
          onBack={() => setStep(0)}
        />
      )}
      {step === 1 && paramsMode === 'manual' && (
        <ProductionForm
          initialParams={params}
          onSubmit={handleParamsSubmit}
          onBack={() => setParamsMode('choose')}
        />
      )}

      {/* Step 2: Distribution */}
      {step === 2 && budget && (
        <CurveAssigner
          budget={budget}
          savedDistributions={distributions}
          onSubmit={handleDistributionsSubmit}
          onBack={() => { setStep(1); setParamsMode('choose'); }}
        />
      )}

      {/* Step 3: Download */}
      {step === 3 && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">
                Download Cashflow
              </h2>
              <p className="text-sm text-gray-500">
                Download the generated cashflow as an Excel file.
              </p>
            </div>
            <button
              onClick={() => setStep(2)}
              className="px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 text-gray-700"
            >
              Back
            </button>
          </div>

          {previewLoading && (
            <div className="flex items-center justify-center py-12">
              <div className="flex flex-col items-center gap-2">
                <div className="animate-spin h-8 w-8 border-2 border-blue-500 border-t-transparent rounded-full" />
                <p className="text-sm text-gray-500">Calculating...</p>
              </div>
            </div>
          )}

          {previewError && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
              {previewError}
            </div>
          )}

          {preview && (
            <div className="flex flex-col items-center gap-6 py-8">
              <div className="bg-white border border-gray-200 rounded-lg p-6 text-center">
                <div className="text-sm text-gray-500 mb-1">Grand Total</div>
                <div className="text-3xl font-bold text-gray-900">
                  {new Intl.NumberFormat('en-AU', { style: 'currency', currency: 'AUD' }).format(preview.grand_total)}
                </div>
              </div>
              {budget && params && distributions.length > 0 && (
                <DownloadButton
                  budget={budget}
                  parameters={params}
                  distributions={distributions}
                />
              )}
            </div>
          )}
        </div>
      )}
    </AppShell>
  );
}
