import React, { useCallback, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { UploadCloud, CheckCircle, AlertTriangle } from 'lucide-react';
import api from '../lib/api';
import { useLang } from '../contexts/LangContext';

type Stage = 'idle' | 'uploading' | 'processing' | 'done' | 'error';

const PAYMENT_METHODS = ['cash', 'bank_transfer', 'cheque', 'credit_card'];

export default function UploadReview() {
  const { t } = useLang();
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [stage, setStage] = useState<Stage>('idle');
  const [result, setResult] = useState<any>(null);
  const [paymentMethod, setPaymentMethod] = useState('');
  const [error, setError] = useState('');

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped) setFile(dropped);
  }, []);

  const upload = async () => {
    if (!file) return;
    setError('');
    setStage('uploading');
    const fd = new FormData();
    fd.append('file', file);
    if (paymentMethod) fd.append('payment_method', paymentMethod);
    try {
      setStage('processing');
      const r = await api.post('/upload', fd, { headers: { 'Content-Type': 'multipart/form-data' } });
      setResult(r.data.data);
      setStage('done');
    } catch (e: any) {
      setError(e.response?.data?.message ?? t('Upload failed.', 'فشل الرفع.'));
      setStage('error');
    }
  };

  const conf = (field: string) => {
    const v = result?.confidence?.[field];
    if (v == null) return null;
    const pct = Math.round(v * 100);
    return (
      <span className={`text-xs font-medium px-1.5 py-0.5 rounded ${
        pct >= 90 ? 'bg-green-100 text-green-700' : pct >= 70 ? 'bg-amber-100 text-amber-700' : 'bg-red-100 text-red-700'
      }`}>{pct}%</span>
    );
  };

  return (
    <div className="space-y-4 max-w-xl">
      <h2 className="text-xl font-semibold text-gray-900">{t('Upload Document', 'رفع مستند')}</h2>

      {/* Drop zone */}
      <div
        onDrop={onDrop}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        className={`border-2 border-dashed rounded-xl p-10 text-center transition-colors cursor-pointer ${
          dragging ? 'border-brand-400 bg-brand-50' : 'border-gray-200 hover:border-brand-300'
        }`}
        onClick={() => document.getElementById('file-input')?.click()}
      >
        <UploadCloud className="mx-auto text-gray-300 mb-3" size={36} />
        <p className="text-sm text-gray-500">
          {file ? file.name : t('Drag & drop or click to select', 'اسحب أو انقر للاختيار')}
        </p>
        <p className="text-xs text-gray-400 mt-1">{t('PDF, PNG, JPG — max 10 MB', 'PDF, PNG, JPG — 10 ميغابايت')}</p>
        <input
          id="file-input" type="file" className="hidden"
          accept=".pdf,.png,.jpg,.jpeg,.webp"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
        />
      </div>

      {/* Payment method */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {t('Payment Method (optional)', 'طريقة الدفع (اختياري)')}
        </label>
        <select value={paymentMethod} onChange={(e) => setPaymentMethod(e.target.value)} className="input">
          <option value="">{t('Not specified', 'غير محدد')}</option>
          {PAYMENT_METHODS.map((m) => <option key={m} value={m}>{m.replace('_', ' ')}</option>)}
        </select>
      </div>

      {error && (
        <div className="px-3 py-2 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700 flex items-center gap-2">
          <AlertTriangle size={14} />{error}
        </div>
      )}

      {stage === 'idle' || stage === 'error' ? (
        <button onClick={upload} disabled={!file} className="btn-primary w-full justify-center">
          {t('Extract & Review', 'استخراج ومراجعة')}
        </button>
      ) : stage === 'uploading' || stage === 'processing' ? (
        <div className="card p-6 text-center text-sm text-gray-500 animate-pulse">
          {stage === 'uploading' ? t('Uploading…', 'جارٍ الرفع…') : t('AI is extracting data…', 'يجري الاستخراج…')}
        </div>
      ) : null}

      {/* Results */}
      {stage === 'done' && result && (
        <div className="card p-5 space-y-4">
          <div className="flex items-center gap-2 text-green-700">
            <CheckCircle size={16} />
            <span className="text-sm font-medium">{t('Extraction complete', 'تم الاستخراج')}</span>
          </div>

          <div className="grid grid-cols-2 gap-3 text-sm">
            {['doc_type', 'document_number', 'party_name', 'document_date', 'total_amount'].map((f) => (
              <div key={f}>
                <div className="flex items-center gap-1.5 mb-0.5">
                  <span className="text-xs text-gray-400 uppercase">{f.replace(/_/g, ' ')}</span>
                  {conf(f)}
                </div>
                <p className="font-medium text-gray-800">{result[f] ?? '—'}</p>
              </div>
            ))}
          </div>

          <div className="flex gap-2 pt-2">
            <button onClick={() => navigate(`/review-queue/${result.id}`)} className="btn-primary">
              {t('Review & Approve', 'مراجعة وموافقة')}
            </button>
            <button onClick={() => { setFile(null); setStage('idle'); setResult(null); }} className="btn-secondary">
              {t('Upload Another', 'رفع آخر')}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
