import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import api from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { MedicalRecord, Appointment, Episode } from '../../types';
import { StatusBadge } from '../../components/doctor/StatusBadge';
import { MarkdownRenderer } from '../../components/MarkdownRenderer';
import {
  ArrowLeft,
  User as UserIcon,
  Mail,
  Phone,
  Calendar,
  FileText,
  Plus,
  ExternalLink,
  ShieldCheck,
  Clock,
  CheckCircle2,
  AlertCircle,
  FileUp,
  X,
  Building,
  Heart,
  Sparkles,
  RefreshCw,
  Activity,
  CheckSquare,
  ChevronDown,
  ChevronUp,
  RotateCw
} from 'lucide-react';

export const DoctorPatientDetailPage: React.FC = () => {
  const { patientId } = useParams<{ patientId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [activeTab, setActiveTab] = useState<'overview' | 'records'>('overview');
  const [patientProfile, setPatientProfile] = useState<any>(null);
  const [records, setRecords] = useState<MedicalRecord[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  // Episode & Summary State
  const [activeEpisode, setActiveEpisode] = useState<Episode | null>(null);
  const [pastEpisodes, setPastEpisodes] = useState<Episode[]>([]);
  const [expandedEpisodeId, setExpandedEpisodeId] = useState<string | null>(null);
  const [resolvingEpisode, setResolvingEpisode] = useState<boolean>(false);

  // Modal State
  const [showUploadModal, setShowUploadModal] = useState<boolean>(false);
  const [title, setTitle] = useState<string>('');
  const [recordType, setRecordType] = useState<string>('diagnosis');
  const [description, setDescription] = useState<string>('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState<boolean>(false);
  const [uploadError, setUploadError] = useState<string>('');
  const [retryingOcrId, setRetryingOcrId] = useState<string | null>(null);

  useEffect(() => {
    if (patientId) {
      fetchPatientData();
    }
  }, [patientId]);

  const fetchEpisodes = async (targetId: string) => {
    try {
      const res = await api.get(`/episodes/patient/${targetId}`);
      if (res?.data) {
        setActiveEpisode(res.data.active_episode || null);
        setPastEpisodes(res.data.past_episodes || []);
      }
    } catch (err) {
      console.error('Failed to fetch patient episodes:', err);
    }
  };

  const fetchPatientData = async () => {
    setLoading(true);
    try {
      const profileRes = await api.get(`/doctors/patients/${patientId}/profile`).catch(() =>
        api.get(`/doctors/me/patients/${patientId}`).catch(() => null)
      );

      const pData = profileRes?.data;
      if (pData) {
        setPatientProfile(pData);
      }

      const targetIds = Array.from(
        new Set(
          [patientId, pData?.patient_id, pData?.profile_id].filter(
            (id): id is string => Boolean(id) && typeof id === 'string'
          )
        )
      );

      const primaryId = targetIds[0] || patientId || '';
      if (primaryId) {
        fetchEpisodes(primaryId);
      }

      const recordPromises = targetIds.map((id) =>
        api.get(`/medical-records/patient/${id}`).catch(() => ({ data: [] }))
      );

      const recordsResponses = await Promise.all(recordPromises);
      const allRecords: MedicalRecord[] = [];
      const seenIds = new Set<string>();

      recordsResponses.forEach((res) => {
        if (Array.isArray(res?.data)) {
          res.data.forEach((r: MedicalRecord) => {
            if (r && r.id && !seenIds.has(r.id)) {
              seenIds.add(r.id);
              allRecords.push(r);
            }
          });
        }
      });

      allRecords.sort((a, b) => {
        const dA = a.created_at ? new Date(a.created_at).getTime() : 0;
        const dB = b.created_at ? new Date(b.created_at).getTime() : 0;
        return dB - dA;
      });

      setRecords(allRecords);
    } catch (err) {
      console.error('Failed to load patient detail data:', err);
    } finally {
      setLoading(false);
    }
  };

  const [refreshingSummary, setRefreshingSummary] = useState<boolean>(false);

  const handleRefreshSummary = async (episodeId: string) => {
    setRefreshingSummary(true);
    try {
      const res = await api.post(`/episodes/${episodeId}/summary/regenerate`);
      if (res?.data?.summary && activeEpisode) {
        setActiveEpisode({
          ...activeEpisode,
          summary: res.data.summary,
          summary_generated_at: res.data.generated_at
        });
      }
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to refresh episode summary');
    } finally {
      setRefreshingSummary(false);
    }
  };

  const handleResolveEpisode = async (episodeId: string) => {
    if (!window.confirm('Mark this clinical episode as resolved? A new active episode will be initiated on next patient intake/upload.')) {
      return;
    }
    setResolvingEpisode(true);
    try {
      await api.post(`/episodes/${episodeId}/resolve`);
      const primaryId = patientProfile?.patient_id || patientId;
      if (primaryId) fetchEpisodes(primaryId);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to resolve episode');
    } finally {
      setResolvingEpisode(false);
    }
  };

  const handleRetryOcr = async (recordId: string) => {
    setRetryingOcrId(recordId);
    try {
      await api.post(`/medical-records/${recordId}/retry-ocr`);
      await fetchPatientData();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to queue OCR retry');
    } finally {
      setRetryingOcrId(null);
    }
  };

  const handleUploadRecord = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      setUploadError('Please select a file to upload (PDF, JPG, PNG, WEBP, max 15MB)');
      return;
    }

    setUploading(true);
    setUploadError('');

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('patient_identifier', patientProfile?.patient_id || patientId || '');
      formData.append('uploaded_by', 'doctor');
      formData.append('title', title);
      formData.append('record_type', recordType);
      if (description) formData.append('description', description);

      await api.post('/medical-records/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      setShowUploadModal(false);
      setTitle('');
      setDescription('');
      setSelectedFile(null);
      setRecordType('diagnosis');
      
      await fetchPatientData();
    } catch (err: any) {
      setUploadError(err.response?.data?.detail || 'Failed to upload medical record');
    } finally {
      setUploading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-16 text-center text-slate-500 flex flex-col items-center gap-3">
        <div className="w-8 h-8 border-3 border-tealmed-500 border-t-transparent rounded-full animate-spin"></div>
        <span>Loading patient clinical details...</span>
      </div>
    );
  }

  const pName = patientProfile?.name || 'Patient Profile';
  const pCode = patientProfile?.patient_code || 'PT-REF';
  const pEmail = patientProfile?.email || 'No email provided';
  const pPhone = patientProfile?.phone || 'No phone provided';
  const appointments: Appointment[] = patientProfile?.appointments || [];

  return (
    <div className="space-y-8 pb-16">
      {/* Back Button & Header */}
      <div>
        <button
          onClick={() => navigate('/doctor/patients')}
          className="inline-flex items-center gap-2 text-xs font-bold text-slate-700 hover:text-tealmed-800 bg-white px-4 py-2 rounded-2xl border border-slate-200 shadow-2xs hover:bg-slate-50 transition-all mb-4"
        >
          <ArrowLeft className="w-4 h-4 text-tealmed-700" /> Back to Patient List
        </button>

        {/* Patient Profile Hero Banner */}
        <div className="bg-gradient-to-r from-tealmed-50 via-emerald-50/70 to-white rounded-3xl p-6 sm:p-8 border border-tealmed-100/90 shadow-2xs flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-tealmed-600 to-tealmed-500 text-white flex items-center justify-center font-extrabold text-2xl border border-tealmed-400 shadow-md">
              {pName.charAt(0).toUpperCase()}
            </div>
            <div className="space-y-1">
              <div className="flex items-center gap-2.5">
                <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900">{pName}</h1>
                <span className="px-3 py-0.5 rounded-full text-xs font-extrabold bg-tealmed-100 text-tealmed-900 border border-tealmed-200">
                  {pCode}
                </span>
              </div>
              <div className="flex flex-wrap items-center gap-4 text-xs font-medium text-slate-600">
                <span className="flex items-center gap-1.5"><Mail className="w-3.5 h-3.5 text-slate-400" /> {pEmail}</span>
                <span className="flex items-center gap-1.5"><Phone className="w-3.5 h-3.5 text-slate-400" /> {pPhone}</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => {
                setActiveTab('records');
                setShowUploadModal(true);
              }}
              className="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2.5 rounded-2xl font-bold text-xs flex items-center gap-2 shadow-md shadow-emerald-600/20 transition-all"
            >
              <Plus className="w-4 h-4" /> Add Medical Record
            </button>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="border-b border-slate-200 flex items-center gap-8">
        <button
          onClick={() => setActiveTab('overview')}
          className={`pb-3 text-xs font-extrabold transition-all border-b-2 flex items-center gap-2 ${
            activeTab === 'overview'
              ? 'border-tealmed-600 text-tealmed-800'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          }`}
        >
          <UserIcon className="w-4 h-4" />
          Overview & Episodes ({activeEpisode ? 1 : 0} Active)
        </button>
        <button
          onClick={() => setActiveTab('records')}
          className={`pb-3 text-xs font-extrabold transition-all border-b-2 flex items-center gap-2 ${
            activeTab === 'records'
              ? 'border-tealmed-600 text-tealmed-800'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          }`}
        >
          <FileText className="w-4 h-4" />
          Medical Records & OCR ({records.length})
        </button>
      </div>

      {/* Tab 1: Overview & Episodes */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Quick Info Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-2xs space-y-1">
              <span className="text-slate-500 text-xs font-bold uppercase tracking-wider">Gender</span>
              <p className="text-sm font-extrabold text-slate-900">{patientProfile?.gender || 'Not specified'}</p>
            </div>
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-2xs space-y-1">
              <span className="text-slate-500 text-xs font-bold uppercase tracking-wider">Blood Group</span>
              <p className="text-sm font-extrabold text-rose-600 flex items-center gap-1">
                <Heart className="w-4 h-4 fill-rose-500 text-rose-500" />
                {patientProfile?.blood_group || 'Not specified'}
              </p>
            </div>
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-2xs space-y-1">
              <span className="text-slate-500 text-xs font-bold uppercase tracking-wider">Active Episode</span>
              <p className="text-sm font-extrabold text-tealmed-800 flex items-center gap-1">
                <Activity className="w-4 h-4 text-tealmed-600" />
                {activeEpisode?.condition || 'General Care'}
              </p>
            </div>
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-2xs space-y-1">
              <span className="text-slate-500 text-xs font-bold uppercase tracking-wider">Total Consultations</span>
              <p className="text-sm font-extrabold text-slate-900">{patientProfile?.consultation_count || appointments.length}</p>
            </div>
          </div>

          {/* Headline Active Episode Summary Card */}
          <div className="bg-gradient-to-br from-teal-50/70 via-white to-emerald-50/50 rounded-3xl border border-tealmed-200/90 p-6 sm:p-8 shadow-2xs space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-tealmed-100/80 pb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-2xl bg-tealmed-600 text-white flex items-center justify-center shadow-md shadow-tealmed-600/20">
                  <Sparkles className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-base font-extrabold text-slate-900">
                      Active Episode: {activeEpisode?.condition || 'General Health Care'}
                    </h3>
                    <span className="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold bg-emerald-100 text-emerald-900 border border-emerald-200 uppercase tracking-wider">
                      Active Episode
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 font-medium mt-0.5">
                    Started: {activeEpisode?.started_at ? new Date(activeEpisode.started_at).toLocaleDateString() : 'Recent'}
                    {activeEpisode?.summary_generated_at ? ` • Summary updated ${new Date(activeEpisode.summary_generated_at).toLocaleTimeString()}` : ''}
                  </p>
                </div>
              </div>

              {activeEpisode && (
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleRefreshSummary(activeEpisode.id)}
                    disabled={refreshingSummary}
                    className="inline-flex items-center gap-1.5 text-xs font-bold text-tealmed-800 bg-white hover:bg-tealmed-50 px-3.5 py-2 rounded-2xl border border-tealmed-200 shadow-2xs transition-all disabled:opacity-50"
                  >
                    <RefreshCw className={`w-3.5 h-3.5 text-tealmed-600 ${refreshingSummary ? 'animate-spin' : ''}`} />
                    {refreshingSummary ? 'Refreshing...' : 'Refresh AI Summary'}
                  </button>

                  <button
                    onClick={() => handleResolveEpisode(activeEpisode.id)}
                    disabled={resolvingEpisode}
                    className="inline-flex items-center gap-1.5 text-xs font-bold text-rose-700 bg-white hover:bg-rose-50 px-3.5 py-2 rounded-2xl border border-rose-200 shadow-2xs transition-all disabled:opacity-50"
                  >
                    <CheckSquare className="w-3.5 h-3.5 text-rose-600" />
                    {resolvingEpisode ? 'Resolving...' : 'Mark Episode Resolved'}
                  </button>
                </div>
              )}
            </div>

            {activeEpisode?.summary ? (
              <div className="bg-white/80 p-6 rounded-2xl border border-tealmed-100/70 shadow-2xs">
                <MarkdownRenderer content={activeEpisode.summary} />
              </div>
            ) : (
              <div className="p-6 text-center bg-slate-50/70 rounded-2xl border border-dashed border-slate-200 text-xs text-slate-500">
                No OCR-extracted summary available yet for this episode. Upload medical documents or chat with AI assistant to synthesize an episode summary.
              </div>
            )}
          </div>

          {/* Past Resolved Episodes Accordion */}
          {pastEpisodes.length > 0 && (
            <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-2xs space-y-4">
              <h3 className="text-base font-extrabold text-slate-900 flex items-center gap-2">
                <Clock className="w-5 h-5 text-slate-500" /> Past Resolved Episodes ({pastEpisodes.length})
              </h3>

              <div className="space-y-3">
                {pastEpisodes.map((ep) => {
                  const isExpanded = expandedEpisodeId === ep.id;
                  return (
                    <div key={ep.id} className="border border-slate-200 rounded-2xl overflow-hidden">
                      <button
                        onClick={() => setExpandedEpisodeId(isExpanded ? null : ep.id)}
                        className="w-full p-4 bg-slate-50 hover:bg-slate-100/80 flex items-center justify-between transition-colors text-left"
                      >
                        <div className="space-y-0.5">
                          <div className="font-bold text-xs text-slate-900">{ep.condition}</div>
                          <div className="text-[10px] text-slate-500 font-medium">
                            Duration: {new Date(ep.started_at).toLocaleDateString()} - {ep.resolved_at ? new Date(ep.resolved_at).toLocaleDateString() : 'Resolved'}
                          </div>
                        </div>
                        <div className="flex items-center gap-3">
                          <span className="px-2 py-0.5 bg-slate-200 text-slate-700 text-[10px] font-bold rounded-full">
                            Resolved
                          </span>
                          {isExpanded ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
                        </div>
                      </button>

                      {isExpanded && (
                        <div className="p-5 bg-white border-t border-slate-100 text-xs space-y-2">
                          <div className="font-semibold text-slate-700">Archived Episode Summary:</div>
                          {ep.summary ? (
                            <MarkdownRenderer content={ep.summary} />
                          ) : (
                            <p className="text-slate-400 italic">No summary archived for this episode.</p>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Appointment History */}
          <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-2xs space-y-4">
            <h3 className="text-base font-extrabold text-slate-900 flex items-center gap-2">
              <Calendar className="w-5 h-5 text-tealmed-600" /> Appointment History
            </h3>

            {appointments.length === 0 ? (
              <div className="p-8 text-center bg-slate-50/70 rounded-2xl border border-dashed border-slate-200 text-xs text-slate-500">
                No past or upcoming appointments recorded for this patient profile.
              </div>
            ) : (
              <div className="divide-y divide-slate-100">
                {appointments.map((app) => (
                  <div key={app.id} className="py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-extrabold text-sm text-slate-900 flex items-center gap-1.5">
                          <Building className="w-4 h-4 text-slate-400" />
                          {app.hospital_name}
                        </span>
                        <StatusBadge status={app.status} />
                      </div>
                      <p className="text-xs text-slate-500">{app.notes || 'Standard medical consultation'}</p>
                    </div>

                    <div className="flex items-center gap-3 text-xs text-slate-600 font-medium">
                      <span className="flex items-center gap-1 bg-slate-50 px-3 py-1 rounded-xl border border-slate-200/80 font-bold text-slate-800">
                        <Calendar className="w-3.5 h-3.5 text-tealmed-600" /> {app.date}
                      </span>
                      <span className="flex items-center gap-1 bg-slate-50 px-3 py-1 rounded-xl border border-slate-200/80 font-semibold text-tealmed-800">
                        <Clock className="w-3.5 h-3.5 text-tealmed-600" /> {app.start_time} - {app.end_time}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 2: Medical Records & OCR */}
      {activeTab === 'records' && (
        <div className="space-y-6">
          <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4 bg-white p-6 rounded-3xl border border-slate-200 shadow-2xs">
            <div>
              <h2 className="text-base font-extrabold text-slate-900 flex items-center gap-2">
                <FileText className="w-5 h-5 text-emerald-600" /> Scoped Medical Records & OCR
              </h2>
              <p className="text-xs text-slate-500">
                Medical reports, lab scans, and document OCR extractions for {pName}.
              </p>
            </div>
            <button
              onClick={() => setShowUploadModal(true)}
              className="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2.5 rounded-2xl font-bold text-xs flex items-center gap-2 transition"
            >
              <Plus className="w-4 h-4" /> Add Record
            </button>
          </div>

          {records.length === 0 ? (
            <div className="bg-white rounded-3xl p-12 text-center text-slate-400 border border-slate-200 space-y-3 shadow-2xs">
              <FileUp className="w-10 h-10 text-slate-300 mx-auto" />
              <p className="text-sm font-semibold text-slate-700">No medical records uploaded for this patient yet.</p>
              <button
                onClick={() => setShowUploadModal(true)}
                className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-50 text-emerald-800 font-bold text-xs rounded-2xl border border-emerald-200/80 hover:bg-emerald-100 transition-colors"
              >
                <Plus className="w-4 h-4" /> Upload First Record
              </button>
            </div>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {records.map((r) => {
                const ocrStatus = r.ocr_status || 'completed';
                return (
                  <div key={r.id} className="bg-white p-6 rounded-3xl border border-slate-200 shadow-2xs space-y-4 hover:shadow-md transition-all flex flex-col justify-between">
                    <div className="space-y-3">
                      <div className="flex justify-between items-start">
                        <span className="text-[10px] font-extrabold px-2.5 py-1 bg-emerald-50 text-emerald-800 rounded-full uppercase tracking-wider border border-emerald-100">
                          {r.record_type ? r.record_type.replace('_', ' ') : 'Record'}
                        </span>
                        
                        {/* OCR Status Badge */}
                        {ocrStatus === 'completed' && (
                          <span className="px-2 py-0.5 bg-emerald-50 text-emerald-700 border border-emerald-200 text-[10px] font-bold rounded-full flex items-center gap-1">
                            <CheckCircle2 className="w-3 h-3 text-emerald-600" /> OCR Ready
                          </span>
                        )}
                        {ocrStatus === 'pending' && (
                          <span className="px-2 py-0.5 bg-amber-50 text-amber-700 border border-amber-200 text-[10px] font-bold rounded-full flex items-center gap-1">
                            <RotateCw className="w-3 h-3 text-amber-600 animate-spin" /> Processing OCR
                          </span>
                        )}
                        {ocrStatus === 'failed' && (
                          <span className="px-2 py-0.5 bg-rose-50 text-rose-700 border border-rose-200 text-[10px] font-bold rounded-full flex items-center gap-1">
                            <AlertCircle className="w-3 h-3 text-rose-600" /> OCR Failed
                          </span>
                        )}
                      </div>

                      <div>
                        <h4 className="font-extrabold text-slate-900 text-base">{r.title}</h4>
                        {r.description && <p className="text-slate-600 text-xs mt-1 leading-relaxed">{r.description}</p>}
                      </div>

                      {/* OCR Extracted Text Preview */}
                      {r.extracted_text && (
                        <div className="p-3 bg-slate-50 rounded-2xl border border-slate-200/80 text-[11px] text-slate-600 max-h-24 overflow-y-auto space-y-1">
                          <div className="font-bold text-slate-800 text-[10px] uppercase tracking-wider">Extracted OCR Text:</div>
                          <p className="whitespace-pre-wrap">{r.extracted_text}</p>
                        </div>
                      )}
                    </div>

                    <div className="space-y-2 pt-3 border-t border-slate-100 text-xs">
                      <div className="flex items-center justify-between text-slate-500 font-medium">
                        <span>Date: {r.created_at ? new Date(r.created_at).toLocaleDateString() : 'Recent'}</span>
                        {r.file_size_bytes && (
                          <span>{(r.file_size_bytes / 1024).toFixed(0)} KB</span>
                        )}
                      </div>

                      {ocrStatus === 'failed' && (
                        <button
                          onClick={() => handleRetryOcr(r.id)}
                          disabled={retryingOcrId === r.id}
                          className="w-full py-2 bg-rose-50 hover:bg-rose-100 text-rose-800 font-bold text-xs rounded-xl flex items-center justify-center gap-1 border border-rose-200 transition-colors"
                        >
                          <RefreshCw className={`w-3.5 h-3.5 text-rose-600 ${retryingOcrId === r.id ? 'animate-spin' : ''}`} />
                          <span>{retryingOcrId === r.id ? 'Queuing Retry...' : 'Retry OCR Processing'}</span>
                        </button>
                      )}

                      {r.signed_file_url ? (
                        <a
                          href={r.signed_file_url}
                          target="_blank"
                          rel="noreferrer"
                          className="w-full py-2.5 px-3 bg-emerald-50 hover:bg-emerald-100 text-emerald-800 font-bold rounded-2xl flex items-center justify-center gap-1.5 border border-emerald-200/80 transition-colors"
                        >
                          <ShieldCheck className="w-4 h-4 text-emerald-700" /> View / Download File <ExternalLink className="w-3.5 h-3.5" />
                        </a>
                      ) : (
                        <span className="text-slate-400 text-xs italic block text-center py-1">No attached document URL</span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Upload Medical Record Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-in fade-in">
          <div className="bg-white rounded-3xl max-w-lg w-full p-6 sm:p-8 space-y-6 shadow-2xl relative border border-slate-100">
            <div className="flex justify-between items-center">
              <div>
                <h3 className="text-lg font-extrabold text-slate-900">Add Medical Record</h3>
                <p className="text-xs text-slate-500">Attached to patient {pName} ({pCode})</p>
              </div>
              <button
                onClick={() => setShowUploadModal(false)}
                className="p-2 text-slate-400 hover:text-slate-600 rounded-xl hover:bg-slate-100"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {uploadError && (
              <div className="p-3.5 bg-rose-50 border border-rose-200 text-rose-800 rounded-2xl text-xs flex items-center gap-2 font-medium">
                <AlertCircle className="w-4 h-4 flex-shrink-0 text-rose-600" />
                <span>{uploadError}</span>
              </div>
            )}

            <form onSubmit={handleUploadRecord} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Record Title *</label>
                <input
                  type="text"
                  required
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Chest X-Ray Report, Blood Test Panel"
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-2xl text-xs font-medium focus:ring-2 focus:ring-emerald-500 outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Record Category</label>
                <select
                  value={recordType}
                  onChange={(e) => setRecordType(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-2xl text-xs font-medium focus:ring-2 focus:ring-emerald-500 outline-none"
                >
                  <option value="diagnosis">Diagnosis Summary</option>
                  <option value="lab_report">Lab Report</option>
                  <option value="xray">X-Ray</option>
                  <option value="mri">MRI Scan</option>
                  <option value="blood_test">Blood Test</option>
                  <option value="discharge_summary">Discharge Summary</option>
                  <option value="other">Other</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Description (Optional)</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={3}
                  placeholder="Clinical notes, findings, or lab observations..."
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-2xl text-xs font-medium focus:ring-2 focus:ring-emerald-500 outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Upload Document (PDF, JPG, PNG, WEBP — max 15MB) *</label>
                <input
                  type="file"
                  required
                  accept=".pdf,.jpg,.jpeg,.png,.webp"
                  onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                  className="w-full px-3.5 py-2 bg-slate-50 border border-slate-200 rounded-2xl text-xs text-slate-600 focus:ring-2 focus:ring-emerald-500"
                />
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowUploadModal(false)}
                  className="px-4 py-2.5 rounded-2xl text-slate-600 font-bold text-xs hover:bg-slate-100 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={uploading}
                  className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs rounded-2xl shadow-md shadow-emerald-600/20 transition-all disabled:opacity-50"
                >
                  {uploading ? 'Uploading...' : 'Upload Record'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
