import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './contexts/AuthContext';
import Layout from './components/Layout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import DocumentList from './pages/DocumentList';
import DocumentDetail from './pages/DocumentDetail';
import PDCDashboard from './pages/PDCDashboard';
import UploadReview from './pages/UploadReview';
import ReviewQueue, { ReviewQueueDetail } from './pages/ReviewQueue';
import AuditLog from './pages/AuditLog';
import Settings from './pages/Settings';

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function RequireOwner({ children }: { children: React.ReactNode }) {
  const { isOwner, loading } = useAuth();
  if (loading) return null;
  if (!isOwner) return <Navigate to="/" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />

      <Route path="/" element={<RequireAuth><Layout /></RequireAuth>}>
        <Route index element={<Dashboard />} />

        <Route path="invoices" element={<DocumentList />} />
        <Route path="purchase-invoices" element={<DocumentList />} />
        <Route path="lpos" element={<DocumentList />} />
        <Route path="quotations" element={<DocumentList />} />
        <Route path="credit-notes" element={<DocumentList />} />
        <Route path="debit-notes" element={<DocumentList />} />
        <Route path="delivery-notes" element={<DocumentList />} />
        <Route path="receipt-vouchers" element={<DocumentList />} />

        <Route path=":docType/:id" element={<DocumentDetail />} />

        <Route path="pdc" element={<PDCDashboard />} />
        <Route path="upload" element={<UploadReview />} />
        <Route path="review-queue" element={<ReviewQueue />} />
        <Route path="review-queue/:id" element={<ReviewQueueDetail />} />

        <Route path="audit-log" element={<RequireOwner><AuditLog /></RequireOwner>} />
        <Route path="settings" element={<RequireOwner><Settings /></RequireOwner>} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
